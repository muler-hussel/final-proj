from pymongo import IndexModel
from app.models.shortlist import ShortlistItem

class PlaceInfo:
  def __init__(self, db):
    self.collection = db["place_info"]

  async def _create_indexes(self):
    await self.collection.create_index("place_name", unique=True)

  async def get_place(self, place_name: str) -> ShortlistItem | None:
    data = await self.collection.find_one({"place_name": place_name})
    if data:
      data.pop("_id", None)  # 避免 Pydantic 校验失败
      return ShortlistItem(**data)
    return None

  async def save_place(self, placeInfo: ShortlistItem):
    await self.collection.replace_one(
      {"place_name": placeInfo.name},
      placeInfo.model_dump(),
      upsert=True
    )