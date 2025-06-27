from app.models.place_info import PlaceInfo
from app.models.shortlist import ShortlistItem

class PlaceInfoService:
  def __init__(self, place_info: PlaceInfo):
    self.place_info = place_info

  async def get_place_info(self, place_name: str):
    return await self.place_info.get_place(place_name)

  async def save_user_preferences(self, place: ShortlistItem):
    await self.place_info.save_place(place)

place_info_service = PlaceInfoService()