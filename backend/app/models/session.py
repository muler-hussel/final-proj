from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict
import uuid

# Infomation shown in drawer
class PlaceInfo(BaseModel):
  image_url: Optional[HttpUrl] = None  # Images retrieved from Google Map, city & attraction
  description: Optional[str] = None # Recommend reason, city & attraction
  website: Optional[HttpUrl] = None # Official website, if is attraction
  address: Optional[str] = None
  open_time: Optional[str] = None
  close_time: Optional[str] = None
  rating: Optional[float] = None
  reviews_summary: Optional[str] = None # Generate by AI
  pros: Optional[List[str]] = []
  contra: Optional[List[str]] = []
  
# Cities, attractions user like
class ShortlistItem(BaseModel):
  name: str
  type: str # 'city' | 'attraction'
  city: Optional[str] = None # If attraction, belongs to which city
  country: Optional[str] = None
  tags: Optional[List[str]] = [] # tags of attraction, 'museum', 'animal', 'history'
  info: Optional[PlaceInfo] = None
  sub_items: Optional[List["ShortlistItem"]] = [] # If city, containing recommended attractions of this city

  class Config:
    arbitrary_types_allowed = True
    from_attributes = True

ShortlistItem.model_rebuild()

# Profile according to preferences in one session. TODO:
class ShortTermProfile(BaseModel):
  preferences: List[str] = []
  shortlist_tags: Dict[str, int] = {}
  clicks: List[str] = []
  view_durations: Dict[str, float] = {}
  prompt_summary: Optional[str] = None

# Infomation not mandatory
class SlotData(BaseModel):
  destination: Optional[str] = None
  date: Optional[str] = None
  people: Optional[str] = None
  preferences: Optional[List[str]] = None

# Items in todo list should have types, 
# so that ai can determine which steps can be completed automatically, 
# while others need user feedback
class TodoItem(BaseModel):
  description: str
  type: str

# Conversation history, slots, 
# reminding user to complete slot, 
# todo list of ai, step ai is about to do, shortlist
class SessionState(BaseModel):
  user_id: str
  session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
  history_key: str = "" # Redis key stores conversation history
  shortlist_key: str = ""
  title: str
  slots: SlotData = SlotData()
  reminded: bool = False
  todo: List[TodoItem] = []
  todo_step: int = 0
  short_term_profile: ShortTermProfile = ShortTermProfile()

  def get_redis_key(self):
    return f"user:{self.user_id}:session:{self.session_id}:metadata"

  def __init__(self, **data):
    super().__init__(**data)
    
    if not self.history_key:
      self.history_key = f"user:{self.user_id}:session:{self.session_id}:history"
    if not self.shortlist_key:
      self.shortlist_key = f"user:{self.user_id}:session:{self.session_id}:shortlist"