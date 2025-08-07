from fastapi import APIRouter, HTTPException, Body
from app.services.redis_service import redis_service
from app.models.recommend import LongTermProfile, UserBehavior
from pydantic import BaseModel
from typing import List
from app.models.shortlist import ShortlistItem
from app.services.recommend_service import recommend_service

class BehaviorTrack(BaseModel):
  userId:str
  sessionId: str
  events: List[UserBehavior]

class PlaceReq(BaseModel):
  place_name: str

class TopicReq(BaseModel):
  user_id: str

router = APIRouter(prefix="/recommend", tags=["recommend"])

# Store user behavior in redis
@router.post("/tracking")
async def save_user_behavior(data: BehaviorTrack = Body(...)):
  session_id = data.sessionId
  user_id = data.userId
  session_state = await redis_service.load_session_state(user_id, session_id)

  if not session_state:
    raise HTTPException(status_code=404, detail="Session not found or expired")
  
  session_state.current_user_behavior = data.events
  await redis_service.save_session_state(session_state)

# Fetch enriched place detail
@router.post("/enrich")
async def get_place_detail(req: PlaceReq = Body(...)) -> ShortlistItem:
  place_name = req.place_name
  
  place = await recommend_service.enrich_place_detail(place_name)

  return place

@router.post("/topics")
async def recommend_topics(req: TopicReq = Body(...)):
  user_id = req.user_id
  topics = await recommend_service.recommend_topics(user_id)

  return topics