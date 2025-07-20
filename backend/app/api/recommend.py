from fastapi import APIRouter, HTTPException, Body
from app.services.redis_service import redis_service
from app.models.recommend import UserBehavior
from pydantic import BaseModel
from typing import List
from app.db.mongodb import get_database
from app.models.db_session import DbSession
from app.models.shortlist import ShortlistItem
from app.services.recommend_service import RecommendService

class BehaviorTrack(BaseModel):
  userId:str
  sessionId: str
  events: List[UserBehavior]

class PlaceReq(BaseModel):
  place_name: str

router = APIRouter(prefix="/recommend", tags=["recommend"])

# Store user behavior in redis
@router.post("/tracking")
async def save_user_behavior(data: BehaviorTrack = Body(...)):
  session_id = data.sessionId
  user_id = data.userId
  session_state = await redis_service.load_session_state(user_id, session_id)

  if not session_state:
    db = await get_database()
    session_state = DbSession(db).get_sesssion(user_id, session_id)
    redis_service.save_session_state(session_state)
  if not session_state:
    raise HTTPException(status_code=404, detail="Session not found or expired")
  
  session_state.current_user_behavior = data.events
  await redis_service.save_session_state(session_state)

# Fetch enriched place detail
@router.post("/enrich")
async def get_place_detail(req: PlaceReq = Body(...)) -> ShortlistItem:
  place_name = req.place_name
  
  db = await get_database()
  place = await RecommendService(db).enrich_place_detail(place_name)

  return place