from app.services.shared import language_model, openai_language_model
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from pydantic import BaseModel
from typing import List, Optional
from app.models.session import SessionState, Message, History
from app.utils.prompts import (
  INTENT_CLASSIFIER_PROMPT,
  PRIMARY_PROMPT,
  GENERATE_SESSION_TITLE_PROMPT,
  BASIC_PROMPT,
)
from app.utils.logger import logger
from app.services.redis_service import redis_service
from app.services.recommend_service import recommend_service
from app.services.itinerary_service import itinerary_service
from app.db.mongodb import get_database
from app.models.db_session import DbSession

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
      PRIMARY_PROMPT
      | language_model
      | StrOutputParser()
    )

    self.basic_chain = (
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
  async def orchestrate_planning_step(self, session_state: SessionState, user_input: str):
    result = None
    if session_state.todo_step == -1:
      db = get_database()
      sessions = await DbSession(db).get_sessions_by_user_id(session_state.user_id)
      session_info = []
      for s in sessions:
        session_info.append({"update_time": s.update_time, "short_term_profile": s.short_term_profile})
      session_info.sort(key=lambda x: x["update_time"], reverse=True)
      await recommend_service.update_longterm_profile(session_state.user_id, session_info)
      result = await recommend_service.recommend_places(session_state, user_input)
      session_state.todo_step = 1
    else:
      # Intent recognition
      classified_intent: List[str] = await self.intent_classifier_chain.ainvoke({
        "user_input": user_input,
      })
      intent_set = set(classified_intent)
      print(classified_intent)
      # logger.info(f"intentions: {classified_intent}")

      # Dispatch different AI according to intent
      if "ADVANCE_STEP" in intent_set:
        session_state.todo_step += 1
        todoType = session_state.todo[session_state.todo_step]
        if todoType == 'Recommend': 
          intent_set.add("MORE_RECOMMENDATIONS")
        elif todoType == 'Draft':
          intent_set.add("ITINERARY_GENERATION")
        else: intent_set.add("FINALIZE_TRIP")

      # New preferences from behavior and input
      session_state = await recommend_service.update_short_term_profile(session_state, user_input)
      
      if ("MORE_RECOMMENDATIONS" in intent_set) or ("MODIFY_PLAN" in intent_set):
        # Prompt for recommend
        session_state.todo_step = 1
        result = await recommend_service.recommend_places(session_state, user_input)
      if "ITINERARY_GENERATION" in intent_set:
        session_state.todo_step = 2
        result = await itinerary_service.create_itinerary(session_state, user_input)
      # If GENERAL_QUERY, AI is free to answer
      if not result and (("GENERAL_QUERY" in intent_set) or ("OTHER" in intent_set)):
        history = await redis_service.get_simplified_history(session_state)
        content: str = await self.basic_chain.ainvoke({
          "user_input": user_input,
          "history": history,
        })
        result = Message(content=content)
        user_history_entry = History(
          role="ai",
          message=result
        )
        await redis_service.append_history(session_state, user_history_entry)
    return result, session_state
  
  async def get_ai_response(self, session_state: SessionState, user_input: str, first_prompt: Optional[str] = None, todo_prompt: Optional[str] = None):   
    user_id = session_state.user_id
    session_id = session_state.session_id
    
    prompt_data = {
      "user_id": user_id,
      "session_id": session_id,
      "first_prompt": first_prompt,
      "todo_prompt": todo_prompt,
      "user_input": user_input,
    }

    response = await self.primary_assistant_chain.ainvoke(prompt_data)
    user_message_content = Message(
      content=response
    )
    user_history_entry = History(
      role="ai",
      message=user_message_content
    )
    await redis_service.append_history(session_state, user_history_entry)
    session_state = await recommend_service.update_short_term_profile(session_state, user_input)
    # logger.info(f"prompt: {prompt_data}, ai response: {response}")
    return {"content": response}, session_state

chat_service = ChatService()