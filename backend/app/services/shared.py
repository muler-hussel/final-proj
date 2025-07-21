import os
from dotenv import load_dotenv
from langchain_openai.chat_models.base import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()
OPENAI_KEY = os.getenv("API_KEY")
GEMINI_KEY = os.getenv("GENIMI_API")

try:
  # Must use ChatOpenAi instead of BaseChatOpenAi for function call. (Seems like BaseChatOpenAi is an interface, but used well before
  language_model = ChatOpenAI(model_name="o4-mini", openai_api_key=OPENAI_KEY)
  language_model = ChatGoogleGenerativeAI(model="gemini-2.0-flash-001", google_api_key=GEMINI_KEY)
except:
  print("Fail to initialize llm")
  raise