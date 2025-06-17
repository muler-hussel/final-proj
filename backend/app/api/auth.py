from fastapi import APIRouter
from app.services.auth_service import AuthService
from app.models.user_profile import UserProfile
from app.db.mongodb import mongodb
from pydantic import BaseModel

class UserCreate(BaseModel):
  userName: str

router = APIRouter(prefix="", tags=["auth"])

@router.post("/login")
async def login(user: UserCreate):
  return await AuthService(UserProfile(mongodb.db)).login(user.userName)