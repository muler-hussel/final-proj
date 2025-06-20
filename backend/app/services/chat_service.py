import os
from dotenv import load_dotenv
from langchain_openai.chat_models.base import BaseChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel
from typing import List, Optional
from app.models.session import SessionState, SlotData
from app.utils.prompts import GENERATE_SESSION_TITLE_PROMPT
from app.utils.prompts import (
    SLOT_FILLING_PROMPT,
    GENERATE_TODO_PROMPT,
    ADJUST_TODO_PROMPT,
    BASIC_PROMPT
)
from app.utils.logger import logger
from app.services.redis_service import redis_service

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

    # Slot fill in
    self.slot_extraction_chain = (
      SLOT_FILLING_PROMPT
      | self.language_model.with_structured_output(SlotDataExtractor)
    )

    # Todo List generate
    self.todo_generation_chain = (
      GENERATE_TODO_PROMPT
      | self.language_model
      | StrOutputParser()
    )

    # Ajust Todo List
    self.todo_adjustment_chain = (
      ADJUST_TODO_PROMPT
      | self.language_model
      | StrOutputParser()
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
  
  # Extract destination, time, people, preferences and others from conversation
  async def extract_slots(self, conversation_history: str) -> SlotData:
    try:
      extractor_output = await self.slot_extraction_chain.ainvoke({"history": conversation_history})
      logger.info(f"prompt: {conversation_history}, extracted preferences: {extractor_output}")
      # None cannot be model_dump
      if extractor_output is None:
        return SlotData()
      return SlotData(**extractor_output.model_dump(exclude_unset=True))
    except Exception as e:
      print(f"Error extracting slots: {e}")
      return SlotData()

  # Initial todo list
  async def generate_initial_todo_list(self, user_id: str, session_id: str, user_input: str) -> List[str]:
    prompt_data = {
      "user_id": user_id,
      "session_id": session_id,
      "user_input": user_input
    }
    todo_list_str = await self.todo_generation_chain.ainvoke(prompt_data)
    logger.info(f"prompt: {user_input}, generated todo list: {todo_list_str}")
    return [step.strip() for step in todo_list_str.split('\n') if step.strip()]

  # Adjust todo list
  async def adjust_todo_list(self, current_todo: List[str], user_input: str) -> List[str]:
    prompt_data = {
      "current_todo": "\n".join([f"{i+1}. {step}" for i, step in enumerate(current_todo)]),
      "user_input": user_input
    }
    adjusted_todo_str = await self.todo_adjustment_chain.ainvoke(prompt_data)
    logger.info(f"prompt: {prompt_data}, adjusted todo list: {adjusted_todo_str}")
    return [step.strip() for step in adjusted_todo_str.split('\n') if step.strip()]

  async def get_ai_response(self, session_state: SessionState, user_input: str, missing_info_prompt: Optional[str] = None) -> str:   
    # TODO: maybe not forward step, maybe not recent 10
    user_id = session_state.user_id
    session_id = session_state.session_id
    current_todo_step_str = f"Current Step: {session_state.todo_step + 1}. {session_state.todo[session_state.todo_step]}" if session_state.todo else "No active todo step."
    history = redis_service.get_history(user_id, session_id)[-10:] # recent 10 conversation
    history_str = "\n".join(f"{msg['role']}: {msg['content']}" for msg in history)

    prompt_data = {
      "user_id": user_id,
      "session_id": session_id,
      "user_input": user_input,
      "missing_info_prompt": missing_info_prompt if missing_info_prompt else "",
      "current_todo_step": current_todo_step_str,
      "history": history_str,
    }

    response = await self.primary_assistant_chain.ainvoke(prompt_data)
    logger.info(f"prompt: {prompt_data}, ai response: {response}")
    return response

chat_service = ChatService()