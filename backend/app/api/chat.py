from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Path, Body
from app.services.redis_service import redis_service
from app.services.chat_service import chat_service
from app.models.session import SessionState, Message, History
import uuid
from typing import Dict, Any
from app.utils.prompts import PROMPT_FIRST_INPUT
from app.db.mongodb import get_database
from app.models.db_session import DbSession
from typing import List

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
  user_id: str
  user_input: str

class AllSessionRes(BaseModel):
  session_id: str
  title: str

class UserIdReq(BaseModel):
  user_id: str

# New chat with or without prompt.
# Suitable for both easy plan and chatting with ai
@router.post("/init", response_model=SessionState)
async def create_session(data: ChatRequest = Body(...)):
  session_id = str(uuid.uuid4())
  user_id = data.user_id
  session_title = f"Trip for {user_id}"
  initial_prompt = data.user_input

  if initial_prompt:
    generated_title = await chat_service.generate_session_title(initial_prompt)
    if generated_title:
      session_title = generated_title
  session_state = SessionState(user_id=user_id, session_id=session_id, title=session_title)
  await redis_service.save_session_state(session_state)
  return session_state

# Get session when refresh or from history chats
@router.post("/{session_id}", response_model=SessionState)
async def get_session(user_id: str, session_id: str = Path(...) ):
  session_state = await redis_service.load_session_state(user_id, session_id)
  if not session_state:
    raise HTTPException(status_code=404, detail="Session not found or expired")
  history = await redis_service.get_history(user_id, session_id)
  shortlist = await redis_service.get_shortlist(session_state)
  response = {
    "messages": history,
    "short_term_profile": session_state.short_term_profile,
    "title": session_state.title,
    "shortlist": shortlist,
  }
  return response

# Get user's all sessions
@router.post("/allSessions", response_model=List[AllSessionRes])
async def get_session_with_userId(req: UserIdReq = Body(...)):
  user_id = req.user_id
  session_info = await redis_service.load_session_with_userId(user_id)
  print(0)
  if len(session_info) == 0:
    db = await get_database()
    sessions = await DbSession(db).get_sessions_by_user_id(user_id)
    print(1)
    if len(session_info) == 0:
      return []
    for s in sessions:
      await redis_service.save_session_state(s)
      session_info.append({"session_id": s.session_id, "title": s.title, "update_time": s.update_time})
    session_info.sort(key=lambda x: x["update_time"], reverse=True)
  return [AllSessionRes(**s) for s in session_info]

# Answer to user prompts, justify todo list, todo step, slots, update session info
@router.post("/{session_id}/res", response_model=Dict[str, Any])
async def chat_with_ai(session_id: str = Path(...), data: ChatRequest = Body(...)):
  user_id = data.user_id
  session_state = await redis_service.load_session_state(user_id, session_id)
  if not session_state:
    db = await get_database()
    session_state = DbSession(db).get_sesssion(user_id, session_id)
    redis_service.save_session_state(session_state)
  if not session_state:
    raise HTTPException(status_code=404, detail="Session not found or expired. Please start a new session.")

  user_input = data.user_input
  user_message_content = Message(
    content=user_input
  )
  user_history_entry = History(
    role="user",
    message=user_message_content
  )
  # update session history with user prompts
  await redis_service.append_history(session_state, user_history_entry)

  todo_step = session_state.todo_step
  first_prompt = None
  ai_response_text = None
  # first prompt
  if todo_step == -1:
    first_prompt = PROMPT_FIRST_INPUT
    todo_step += 1
    session_state.todo_step = todo_step
    ai_response_text, session_state = await chat_service.get_ai_response(
      session_state, user_input, first_prompt, session_state.todo[todo_step]
    )
  else:
    ai_response_text, session_state = await chat_service.orchestrate_planning_step(session_state, user_input)
  
  await redis_service.save_session_state(session_state)
  response = {
    "role": "ai",
    "message": ai_response_text,
    "short_term_profile": session_state.short_term_profile
  }
  
  return response