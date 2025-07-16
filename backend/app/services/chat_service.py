from app.services.shared import language_model
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from pydantic import BaseModel
from typing import List, Optional
from app.models.session import SessionState, Message, History
from app.utils.prompts import (
  CREATE_ITINERARY_PROMPT,
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

    self.create_itinerary_chain = (
      CREATE_ITINERARY_PROMPT
      | language_model
      | JsonOutputParser(pydantic_object=Message)
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
    user_message_content = Message(
      content=user_input
    )
    user_history_entry = History(
      role="user",
      message=user_message_content
    )
    await redis_service.append_history(session_state, user_history_entry)

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
      todoType = session_state.todo[session_state.todo_step]
      if todoType == 'Recommend': 
        intent_set.add("MORE_RECOMMENDATIONS")
      elif todoType == 'Draft':
        intent_set.add("ITINERARY_GENERATION")
      else: intent_set.add("FINALIZE_TRIP")

    db = await get_database()
    recommend_service = RecommendService(db)
    # New preferences from behavior and input
    session_state = await recommend_service.update_short_term_profile(session_state, user_input)
    
    if ("MORE_RECOMMENDATIONS" in intent_set) or ("MODIFY_PLAN" in intent_set):
      # Prompt for recommend
      result = await recommend_service.recommend_places(session_state, user_input)
    elif "ITINERARY_GENERATION" in intent_set:
      result = await self.create_itinerary(session_state, user_input)
    elif "FINALIZE_TRIP" in intent_set:
      result = await self.get_ai_response(session_state, user_input, None, session_state.todo_step)
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
    db = await get_database()
    recommend_service = RecommendService(db)
    session_state = await recommend_service.update_short_term_profile(session_state, user_input)
    # logger.info(f"prompt: {prompt_data}, ai response: {response}")
    return {"content": response}, session_state

  async def create_itinerary(self, session_state: SessionState, user_input: str):
    history = (await redis_service.get_history(session_state.user_id, session_state.session_id))[-10:]
    history_str = "\n".join(f"{msg.role}: {msg.message}" for msg in history)
    shortlist = await redis_service.get_shortlist(session_state)
    place_names = ",".join(f"{s.name}: {s.info.weekday_text}" for s in shortlist)
    
    prompt_data = {
      "history": history_str,
      "place_names":  place_names,
      "user_input": user_input,
    }
    response: Message = await self.create_itinerary_chain.ainvoke(prompt_data)
    user_history_entry = History(
      role="ai",
      message=response
    )
    await redis_service.append_history(session_state, user_history_entry)
    return response

chat_service = ChatService()