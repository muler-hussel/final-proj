from app.models.user_profile import UserProfile

class AuthService:
  def __init__(self, user_profile: UserProfile):
    self.user_profile = user_profile

  async def login(self, username: str):
    user = await self.user_profile.get_user(username)
    if not user:
      return str(await self.user_profile.create_user(username))
    return str(user["_id"])