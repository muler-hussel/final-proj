from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Path, Body
from app.services.redis_service import redis_service
from app.services.chat_service import chat_service
from app.models.session import SessionState, SlotData
import uuid
from typing import Dict, Any
from app.utils.prompts import MISSING_SLOT_PROMPT_FIRST_INPUT, MISSING_SLOT_PROMPT_BEFORE_PLANNING

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
  user_id: str
  user_input: str

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
  redis_service.save_session_state(session_state)
  return session_state

# Get session when refresh or from history chats
@router.get("/{session_id}", response_model=SessionState)
async def get_session(session_id: str = Path(...), data: ChatRequest = Body()):
  user_id = data.user_id
  session_state = redis_service.load_session_state(user_id, session_id)
  if not session_state:
    raise HTTPException(status_code=404, detail="Session not found or expired")
  return session_state

# Answer to user prompts, justify todo list, todo step, slots, update session info
@router.post("/{session_id}/res", response_model=Dict[str, Any])
async def chat_with_ai(session_id: str = Path(...), data: ChatRequest = Body(...)):
  user_id = data.user_id
  session_state = redis_service.load_session_state(user_id, session_id)
  if not session_state:
    raise HTTPException(status_code=404, detail="Session not found or expired. Please start a new session.")

  user_input = data.user_input
  # update session history with user prompts
  redis_service.append_history(user_id, session_id, user_input, "user")

  # slot extract
  extracted_slots_from_input = await chat_service.extract_slots(user_input)
  if extracted_slots_from_input:
    session_state = redis_service.update_slots(user_id, session_id, extracted_slots_from_input)
    if not session_state:
      raise HTTPException(status_code=500, detail="Failed to update session slots.")

  # Todo List
  # first prompt
  is_first_user_input = 1
  if not session_state.todo:
    session_state.todo = await chat_service.generate_initial_todo_list(
      user_id, session_id, user_input
    )
    session_state.todo_step = 0
    redis_service.save_session_state(session_state)
  # TODO: extract todo from prompts, adjust todolist, adjust todostep
  else:
    is_first_user_input = 0
    adjusted_todo = await chat_service.adjust_todo_list(
      session_state.todo, user_input
    )
    if adjusted_todo != session_state.todo:
      session_state.todo = adjusted_todo
      redis_service.save_session_state(session_state)

  # When first prompt arrives or before create a trip, remind of completing slots
  missing_info_prompt = None
  if not check_slots_complete(session_state.slots):
    if is_first_user_input:
      missing_info_prompt = MISSING_SLOT_PROMPT_FIRST_INPUT
    else:
      generate_route_index = -2
      try:
        generate_route_index = session_state.todo.index("Draft a detailed itinerary")
      except ValueError:
        pass
      if generate_route_index != -2 and session_state.todo_step >= generate_route_index - 1:
        if not session_state.reminded:
          missing_info_prompt = MISSING_SLOT_PROMPT_BEFORE_PLANNING.format(
            destination=session_state.slots.destination or "Not provided",
            date=session_state.slots.date or "Not provided",
            people=session_state.slots.people or "Not provided",
            preferences=", ".join(session_state.slots.preferences) if session_state.slots.preferences else "Not provided"
          )
        session_state.reminded = True
        redis_service.save_session_state(session_state)

  # Ai response, update session history
  ai_response_text = await chat_service.get_ai_response(
    session_state, user_input, missing_info_prompt
  )
  redis_service.append_history(user_id, session_id, ai_response_text, "ai")

  response = {
    "user_id": user_id,
    "session_id": session_id,
    "ai_response": {
      "role": "ai",
      "content": ai_response_text,
    },
    "current_slots": session_state.slots.model_dump(),
    "current_todo": session_state.todo,
    "current_todo_step_index": session_state.todo_step,
    "history": redis_service.get_history(user_id, session_id)
  }
  return response

# TODO:shortlist
def check_slots_complete(slots: SlotData) -> bool:
  return all([
    slots.destination is not None,
    slots.date is not None,
    slots.people is not None,
    slots.preferences is not None and len(slots.preferences) > 0
  ])