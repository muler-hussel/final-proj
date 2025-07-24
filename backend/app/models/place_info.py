import asyncio
from pymongo import IndexModel
from app.models.shortlist import ShortlistItem

class PlaceInfo:
  def __init__(self, db):
    self.collection = db["place_info"]
    self._init_task = asyncio.create_task(self._create_indexes())

  async def _create_indexes(self):
    await self.collection.create_indexes([
      IndexModel([("name", 1)], unique=True)
    ])

  async def get_place(self, place_name: str) -> ShortlistItem | None:
    data = await self.collection.find_one({"name": place_name})
    if data:
      data.pop("_id", None)
      return ShortlistItem(**data)
    return None

  async def save_place(self, placeInfo: ShortlistItem):
    await self.collection.replace_one(
      {"name": placeInfo.name},
      placeInfo.model_dump(),
      upsert=True
    )