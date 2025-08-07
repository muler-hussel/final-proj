import asyncio
from datetime import datetime
from pydantic import BaseModel
from pymongo import IndexModel, ASCENDING
from typing import Optional
from app.models.survey import SurveyResponse

class ConsentStatus(BaseModel):
  is_consented: bool
  survey_completed: bool

class UserSurvey:
  def __init__(self, db):
    self.collection = db["survey"]
    self._init_task = asyncio.create_task(self._create_indexes())

  async def _create_indexes(self):
    await self.collection.create_indexes([
      IndexModel([("expire_at", ASCENDING)], expireAfterSeconds=0),
      IndexModel([("user_id", ASCENDING)], unique = True)
    ])

  async def is_consented(self, user_id: str) -> ConsentStatus:
    result = await self.collection.find_one({"user_id": user_id}, {"is_consented": 1, "survey_completed": 1})
    return {
      "is_consented": result.get("is_consented", False) if result else False,
      "survey_completed": result.get("survey_completed", False) if result else False
    }
  
  async def save_consent(self, user_id: str, consent_hash: str):
    await self.collection.update_one(
      {"user_id": user_id},
      {"$set": {"is_consented": True, "consent_hash": consent_hash, "expire_at": datetime(2025,12,31,0,0,0)}},
      upsert=True
    )
  
  async def save_survey_response(self, user_id: str, response: SurveyResponse):
    await self.collection.update_one(
      {"user_id": user_id},
      {"$set": {"survey_completed": True, "survey_response": response.model_dump()}},
      upsert=True
    )