from pydantic import BaseModel, Field
from typing import List, Optional, Set, Literal
import uuid
from app.models.recommend import ShortTermProfile, UserBehavior
from app.models.shortlist import ShortlistItem
from datetime import datetime

class Extend(BaseModel):
  openingHours: List[str]
  type: str

class DiscardPlace(BaseModel):
  name: str
  duration: int
  extendedProps: Extend

class DailyItinerary(BaseModel):
  date: int
  type: Literal['visit', 'commute']
  place_name: Optional[str] = None
  start_time: str
  end_time: str
  commute_mode: Optional[str] = None
  discarded_places: Optional[List[DiscardPlace]] = []

class Message(BaseModel):
  content: str
  recommendations: Optional[List[ShortlistItem]] = []
  populars: Optional[List[ShortlistItem]] = []
  itinerary: Optional[List[DailyItinerary]] = []

class History(BaseModel):
  role: str
  message: Message

class SessionState(BaseModel):
  user_id: str
  session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
  history_key: str = "" # Redis key stores conversation history
  shortlist_key: str = ""
  title: str
  todo: List[str] = ["Init", "Recommend", "Draft", "Final trip"]
  todo_step: int = -1
  short_term_profile: ShortTermProfile = ShortTermProfile()
  current_user_behavior: Optional[List[UserBehavior]] = None
  recommended_places: List[str] = []
  history: Optional[List[History]] = []
  shortlist: Optional[List[ShortlistItem]] = []
  update_time: Optional[datetime] = None

  def get_redis_key(self):
    return f"user:{self.user_id}:session:{self.session_id}:metadata"

  def __init__(self, **data):
    super().__init__(**data)
    
    if not self.history_key:
      self.history_key = f"user:{self.user_id}:session:{self.session_id}:history"
    if not self.shortlist_key:
      self.shortlist_key = f"user:{self.user_id}:session:{self.session_id}:shortlist"
  
  @property
  def recommended_places_set(self) -> Set[str]:
      return set(self.recommended_places)

  def add_recommended_places(self, item: str):
      current = set(self.recommended_places)
      current.update(item)
      self.recommended_places = list(current)