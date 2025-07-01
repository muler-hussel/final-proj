from fastapi import APIRouter, HTTPException, Body
from app.services.redis_service import redis_service
from app.models.recommend import UserBehavior
from pydantic import BaseModel
from typing import List

class BehaviorTrack(BaseModel):
  userId:str
  sessionId: str
  events: List[UserBehavior]

router = APIRouter(prefix="/recommend", tags=["recommend"])

# Store user behavior in redis
@router.post("/tracking")
async def save_user_behavior(data: BehaviorTrack = Body(...)):
  session_id = data.sessionId
  user_id = data.user_id
  
  session_state = await redis_service.load_session_state(user_id, session_id)

  if not session_state:
    raise HTTPException(status_code=404, detail="Session not found or expired")
  
  session_state.current_user_behavior = data.events
  redis_service.save_session_state(session_state)