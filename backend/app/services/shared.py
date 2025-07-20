import os
from dotenv import load_dotenv
from langchain_openai.chat_models.base import BaseChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()
OPENAI_KEY = os.getenv("API_KEY")
GEMINI_KEY = os.getenv("GENIMI_API")

try:
  language_model = BaseChatOpenAI(model_name="gpt-4o-mini", openai_api_key=OPENAI_KEY)
  language_model = ChatGoogleGenerativeAI(model="gemini-2.0-flash-001", google_api_key=GEMINI_KEY)
except:
  print("Fail to initialize llm")
  raise