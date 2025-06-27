import os
from dotenv import load_dotenv
from langchain_openai.chat_models.base import BaseChatOpenAI
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
from app.services.recommend_service import recommend_service

class SlotDataExtractor(BaseModel):
  destination: Optional[str]
  date: Optional[str]
  people: Optional[str]
  preferences: Optional[List[str]]

class ChatService:
  def __init__(self):
    # if not os.environ.get("GEMINI_API_KEY"):
    #   os.environ["GEMINI_API_KEY"] = getpass.getpass("Enter API key for Google Gemini: ")
    # try:
    #   self.language_model = ChatGoogleGenerativeAI(model="gemini-2.5-flash-preview-05-20")
    # if not os.environ.get("OPENAI_API_KEY"):
    #   os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter API key for OpenAI: ")
    load_dotenv()
    OPENAI_KEY = os.getenv("API_KEY")
    
    try:
      self.language_model = BaseChatOpenAI(model_name="gpt-4o-mini", openai_api_base="https://free.v36.cm/v1", openai_api_key=OPENAI_KEY)
    except:
      print("Fail to initialize llm")
      raise
    
    # Generate title according to prompt
    self.title_generation_chain = (
      GENERATE_SESSION_TITLE_PROMPT 
      | self.language_model 
      | StrOutputParser()
    )

    self.intent_classifier_chain = (
      INTENT_CLASSIFIER_PROMPT
      | self.language_model
      | JsonOutputParser()
    )

    self.primary_assistant_chain = (
      BASIC_PROMPT
      | self.language_model
      | StrOutputParser()
    )

  # Automatically generate trip title
  async def generate_session_title(self, prompt: str) -> str:
    try:
      generated_title = await self.title_generation_chain.ainvoke({"prompt": prompt})
      logger.info(f"prompt: {prompt}, generated title: {generated_title}")
      return generated_title.strip('"').strip()
    except Exception as e:
      print(f"Error generating session title: {e}")
      return "New Trip"
  
  # Processing prompt
  async def orchestrate_planning_step(self, session_state: SessionState, user_input: str) -> int:
    user_id = session_state.user_id
    session_id = session_state.session_id
    # Append input into conversation history
    await redis_service.append_history(session_state, user_input, "user")

    # Intent recognition
    classified_intent: List[str] = await self.intent_classifier_chain.ainvoke({
      "user_input": user_input,
    })
    intent_set = set(classified_intent)
    logger.info(f"prompt: {user_input}, intentions: {classified_intent}")

    # Dispatch different AI according to intent
    # If GENERAL_QUERY, AI is free to answer
    if "ADVANCE_STEP" in intent_set:
      session_state.todo_step += 1
    
    if "MORE_RECOMMENDATIONS" or "MODIFY_PLAN" in intent_set:
      # Summarize user preferences
      # short term + input + user behave
      short_term_profile = session_state.short_term_profile
      # Prompt for recommend
      result = await self.intent_classifier_chain.ainvoke({
        "user_input": user_input,
      })
    elif "ITINERARY_GENERATION" in intent_set:
      result = await self.get_ai_response(session_state, user_input, None, session_state.todo_step)
    elif "FINALIZE_TRIP" in intent_set:
      result = await self.get_ai_response(session_state, user_input, None, session_state.todo_step)
    return result
  
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
    logger.info(f"prompt: {prompt_data}, ai response: {response}")
    return response

chat_service = ChatService()