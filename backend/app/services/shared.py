import os
from dotenv import load_dotenv
from langchain_openai.chat_models.base import BaseChatOpenAI

load_dotenv()
OPENAI_KEY = os.getenv("API_KEY")

try:
  language_model = BaseChatOpenAI(model_name="gpt-4o-mini", openai_api_base="https://free.v36.cm/v1", openai_api_key=OPENAI_KEY)
except:
  print("Fail to initialize llm")
  raise