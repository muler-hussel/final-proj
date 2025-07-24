import asyncio
from pymongo import IndexModel
from app.models.recommend import LongTermProfile

class UserPreference:
  def __init__(self, db):
    self.collection = db["user_preferences"]
    self._init_task = asyncio.create_task(self._create_indexes())

  async def _create_indexes(self):
    await self.collection.create_indexes([
      IndexModel([("user_id", 1)], unique=True)
    ])

  async def get_preference(self, user_id: str) -> LongTermProfile | None:
    data = await self.collection.find_one({"user_id": user_id})
    return LongTermProfile(**data) if data else None

  async def save_preference(self, profile: LongTermProfile):
    await self.collection.replace_one(
      {"user_id": profile.user_id},
      profile.model_dump(),
      upsert=True
    )

  async def delete_preference(self, user_id: str):
    await self.collection.delete_one({"user_id": user_id})
