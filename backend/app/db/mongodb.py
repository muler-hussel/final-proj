from pymongo.errors import ConnectionFailure
from pymongo import AsyncMongoClient
from app.models.user_profile import UserProfile
from app.models.user_preference import UserPreference
from app.models.place_info import PlaceInfo
from app.models.db_session import DbSession
from app.models.user_survey import UserSurvey
import os
from dotenv import load_dotenv

class MongoDB:
  def __init__(self):
    self.client = None
    self.db = None
    self.user_profile = None
    self.user_preference = None
    self.place_info = None
    self.session = None
    self.survey = None

  async def connect(self):
    """connect mongodb"""
    load_dotenv()
    try:
      self.client = AsyncMongoClient(os.getenv("MONGODB_URI"))
      self.db = self.client.get_database("yourtravel")
      self.user_profile = UserProfile(self.db)
      self.user_preference = UserPreference(self.db)
      self.place_info = PlaceInfo(self.db)
      self.session = DbSession(self.db)
      self.survey = UserSurvey(self.db)
      await self.client.admin.command('ping') 
      print("Successfully connected to MongoDB!")
    except ConnectionFailure as e:
      print(f"Fail to connect to mongodb: {e}")
      raise

  async def close(self):
    """close connection to db"""
    if self.client:
      await self.client.close()
      print("MongoDB connection closed.")

mongodb = MongoDB()

def get_database():
  if mongodb.db is None:
    raise RuntimeError("Database not connected. Call connect_to_mongo() first.")
  return mongodb.db