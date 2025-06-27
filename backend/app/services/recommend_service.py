from app.models.user_preference import UserPreference
from backend.app.models.recommend import LongTermProfile

class RecommendService:
  def __init__(self, user_preference: UserPreference):
    self.user_preference = user_preference

  async def get_long_preferences(self, user_id: str):
    return await self.user_preference.get_preference(user_id)

  async def save_long_preferences(self, profile: LongTermProfile):
    await self.user_preference.save_preference(profile)

  async def clear_long_preferences(self, user_id: str):
    await self.user_preference.delete_preference(user_id)

  
recommend_service = RecommendService()