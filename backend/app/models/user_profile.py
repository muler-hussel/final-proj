import asyncio
from pymongo import IndexModel
from bson import ObjectId

class UserProfile:
  def __init__(self, db):
    self.collection = db["user_profile"]
    self._init_task = asyncio.create_task(self._create_indexes())

  async def _create_indexes(self):
    await self.collection.create_indexes([
      IndexModel([("userName", 1)], unique=True)
    ])

  async def create_user(self, username: str):
    result = await self.collection.insert_one({
      "_id": ObjectId(),
      "username": username,
    })
    return result.inserted_id
  
  async def get_user(self, username: str):
    return await self.collection.find_one({"username": username})