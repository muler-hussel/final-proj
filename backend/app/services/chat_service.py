import os
from dotenv import load_dotenv
from langchain_openai.chat_models.base import BaseChatOpenAI
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from pydantic import BaseModel, ValidationError
from typing import List, Optional
from app.models.session import SessionState, SlotData, TodoItem
from app.utils.prompts import GENERATE_SESSION_TITLE_PROMPT
from app.utils.prompts import (
    SLOT_FILLING_PROMPT,
    GENERATE_TODO_PROMPT,
    ADJUST_TODO_PROMPT,
    INTENT_CLASSIFIER_PROMPT,
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
      | self.language_model
      | JsonOutputParser(pydantic_object=SlotData)
    )

    # Todo List generate
    self.todo_generation_chain = (
      GENERATE_TODO_PROMPT
      | self.language_model
      | JsonOutputParser()
    )

    # Ajust Todo List
    self.todo_adjustment_chain = (
      ADJUST_TODO_PROMPT
      | self.language_model
      | JsonOutputParser()
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
  
  # Extract destination, time, people, preferences and others from conversation
  async def extract_slots(self, conversation_history: str, cur_slot: Optional[SlotData] = None) -> SlotData:
    try:
      extractor_output = await self.slot_extraction_chain.ainvoke({
        "history": conversation_history,
        "cur_slot": cur_slot
      })
      logger.info(f"prompt: {conversation_history}{cur_slot}, extracted preferences: {extractor_output}")
      # None cannot be model_dump
      if extractor_output is None:
        return SlotData()
      return SlotData.model_validate(extractor_output)
    except Exception as e:
      print(f"Error extracting slots: {e}")
      return SlotData()

  # Initial todo list
  async def generate_initial_todo_list(self, user_id: str, session_id: str, user_input: str) -> List[TodoItem]:
    prompt_data = {
      "user_id": user_id,
      "session_id": session_id,
      "user_input": user_input
    }
    todo_list_raw = await self.todo_generation_chain.ainvoke(prompt_data)
    try:
      todo_list = [TodoItem(**item) for item in todo_list_raw]
    except ValidationError as e:
      logger.warning(f"Failed to parse todo items: {e}")
      todo_list = []
    
    todo_list_str = "\n".join(str(item) for item in todo_list)
    logger.info(f"prompt: {user_input}, generated todo list:\n{todo_list_str}")
    return todo_list
  
  # Processing prompt
  async def orchestrate_planning_step(self, user_id: str, session_id: str, user_input: str) -> int:
    session_state = await redis_service.load_session_state(user_id, session_id)

    # Append input into conversation history
    await redis_service.append_history(user_id, session_id, user_input, "user")

    cur_slot = session_state.slots.model_dump_json()
    # Intention recognition
    classified_intent: List[str] = await self.intent_classifier_chain.ainvoke({
      "user_input": user_input,
      "existing_slots_json": cur_slot
    })
    logger.info(f"prompt: {user_input}, existing slots: {cur_slot}, intentions: {classified_intent}")

    # Try to update slots
    new_slots_data: SlotData = await self.extract_slots(user_input, cur_slot)
    await redis_service.update_slots(user_id, session_id, new_slots_data)

    # Ajust todo list according to intention
    adjustment_output = await self.todo_adjustment_chain.ainvoke({
      "user_id": user_id,
      "session_id": session_id,
      "slots": session_state.slots.model_dump_json(),
      "current_todo_list": [item.model_dump() for item in session_state.todo],
      "current_step_index": session_state.todo_step,
      "user_input": user_input,
      "intent": classified_intent,
    })
    session_state.todo = [TodoItem(**item) for item in adjustment_output["new_todo_list"]]
    session_state.todo_step = adjustment_output["new_current_step_index"]
    final_step = adjustment_output["final_step_index"]
    logger.info(f"prompt: {user_input}, intent: {classified_intent}, new_todo_list: {session_state.todo}, todo_step:{session_state.todo_step}, final_step:{final_step}")
    await redis_service.save_session_state(session_state)

    return final_step

  # Executing one or several steps
  async def get_ai_response(self, session_state: SessionState, user_input: str, missing_info_prompt: Optional[str] = None, todo_prompt: Optional[str] = None) -> str:   
    user_id = session_state.user_id
    session_id = session_state.session_id
    history = (await redis_service.get_history(user_id, session_id))[-10:] # recent 10 conversation
    history_str = "\n".join(f"{msg['role']}: {msg['message']}" for msg in history)
    
    prompt_data = {
      "user_id": user_id,
      "session_id": session_id,
      "history": history_str,
      "missing_info_prompt": missing_info_prompt,
      "todo_prompt": todo_prompt,
      "user_input": user_input,
    }

    response = await self.primary_assistant_chain.ainvoke(prompt_data)
    logger.info(f"prompt: {prompt_data}, ai response: {response}")
    return response

chat_service = ChatService()