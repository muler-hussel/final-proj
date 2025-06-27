from pymongo import IndexModel
from app.models.shortlist import ShortlistItem

class PlaceInfo:
  def __init__(self, db):
    self.collection = db["place_info"]

  async def _create_indexes(self):
    await self.collection.create_indexes([
      IndexModel([("place_name", 1)], unique=True)
    ])

  async def get_place(self, place_name: str) -> ShortlistItem | None:
    data = await self.collection.find_one({"place_name": place_name})
    return ShortlistItem(**data) if data else None

  async def save_place(self, placeInfo: ShortlistItem):
    await self.collection.replace_one(
      {"place_name": placeInfo.place_name},
      placeInfo.model_dump(),
      upsert=True
    )