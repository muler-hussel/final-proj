from app.services.shared import language_model
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from pydantic import BaseModel
from typing import List, Optional
from app.models.session import SessionState
from app.utils.prompts import (
  INTENT_CLASSIFIER_PROMPT,
  BASIC_PROMPT,
  GENERATE_SESSION_TITLE_PROMPT
)
from app.utils.logger import logger
from app.services.redis_service import redis_service
from app.services.recommend_service import RecommendService
from app.db.mongodb import get_database

class SlotDataExtractor(BaseModel):
  destination: Optional[str]
  date: Optional[str]
  people: Optional[str]
  preferences: Optional[List[str]]

class ChatService:
  def __init__(self):
    # Generate title according to prompt
    self.title_generation_chain = (
      GENERATE_SESSION_TITLE_PROMPT 
      | language_model 
      | StrOutputParser()
    )

    self.intent_classifier_chain = (
      INTENT_CLASSIFIER_PROMPT
      | language_model
      | JsonOutputParser()
    )

    self.primary_assistant_chain = (
      BASIC_PROMPT
      | language_model
      | StrOutputParser()
    )

  # Automatically generate trip title
  async def generate_session_title(self, prompt: str) -> str:
    try:
      generated_title = await self.title_generation_chain.ainvoke({"prompt": prompt})
      # logger.info(f"prompt: {prompt}, generated title: {generated_title}")
      return generated_title.strip('"').strip()
    except Exception as e:
      print(f"Error generating session title: {e}")
      return "New Trip"
  
  # Processing prompt
  async def orchestrate_planning_step(self, session_state: SessionState, user_input: str) -> int:
    # Append input into conversation history
    await redis_service.append_history(session_state, user_input, "user")

    # Intent recognition
    classified_intent: List[str] = await self.intent_classifier_chain.ainvoke({
      "user_input": user_input,
    })
    intent_set = set(classified_intent)
    # logger.info(f"prompt: {user_input}, intentions: {classified_intent}")

    # Dispatch different AI according to intent
    # If GENERAL_QUERY, AI is free to answer
    if "ADVANCE_STEP" in intent_set:
      session_state.todo_step += 1
    
    if "MORE_RECOMMENDATIONS" or "MODIFY_PLAN" in intent_set:
      db = await get_database()
      recommend_service = RecommendService(db)
      # New preferences from behavior and input
      session_state = await recommend_service.update_short_term_profile(session_state, user_input)
      # Prompt for recommend
      result = await recommend_service.recommend_places(session_state, user_input)
    elif "ITINERARY_GENERATION" in intent_set:
      result = await self.get_ai_response(session_state, user_input, None, session_state.todo_step)
    elif "FINALIZE_TRIP" in intent_set:
      result = await self.get_ai_response(session_state, user_input, None, session_state.todo_step)
    return result, session_state
  
  # Executing one or several steps
  async def get_ai_response(self, session_state: SessionState, user_input: str, first_prompt: Optional[str] = None, todo_prompt: Optional[str] = None) -> str:   
    user_id = session_state.user_id
    session_id = session_state.session_id
    history = (await redis_service.get_history(user_id, session_id))[-10:] # recent 10 conversation
    history_str = "\n".join(f"{msg['role']}: {msg['message']}" for msg in history)
    
    prompt_data = {
      "user_id": user_id,
      "session_id": session_id,
      "history": history_str,
      "first_prompt": first_prompt,
      "todo_prompt": todo_prompt,
      "user_input": user_input,
    }

    response = await self.primary_assistant_chain.ainvoke(prompt_data)
    await redis_service.append_history(session_state, response, "ai")
    db = await get_database()
    recommend_service = RecommendService(db)
    session_state = await recommend_service.update_short_term_profile(session_state, user_input)
    # logger.info(f"prompt: {prompt_data}, ai response: {response}")
    return {"content": response}, session_state

chat_service = ChatService()