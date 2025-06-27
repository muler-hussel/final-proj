from pydantic import BaseModel
from typing import List, Optional, Dict, Literal

class TagWeight(BaseModel):
  tag: str
  weight: float
  # Decaying_preferences mentioned consecutivly in 2 sessions, moved into verified_preferences
  # Verified_preferences not mentioned consecutivly in 3 sessions, moved into decaying_preferences
  consecutive_sessions: Optional[int]

# Profile according to preferences in one session. TODO:
class ShortTermProfile(BaseModel):
  preferences: Optional[List[TagWeight]] = None
  avoids: Optional[List[TagWeight]] = None
  clicks: List[str] = []
  view_durations: Dict[str, float] = {}
  prompt_summary: Optional[str] = None

class LongTermProfile(BaseModel):
  user_id: str
  verified_preferences: Optional[List[TagWeight]] = None
  decaying_preferences: Optional[List[TagWeight]] = None
  avoids: Optional[List[TagWeight]] = None

class UserBehavior(BaseModel):
  place_name: str # Name of place card user acts
  event_type: Literal["click", "view", "shortlist"]  # Type of behavior
  duration_sec: Optional[float] # Viewing time