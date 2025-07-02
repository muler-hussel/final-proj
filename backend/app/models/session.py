from pydantic import BaseModel, Field
from typing import List, Optional, Set
import uuid
from app.models.recommend import ShortTermProfile, UserBehavior

class SessionState(BaseModel):
  user_id: str
  session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
  history_key: str = "" # Redis key stores conversation history
  shortlist_key: str = ""
  title: str
  todo: List[str] = ["Init", "Recommend places for user", "Draft an itinerary for user to modify", "Generate a final trip"]
  todo_step: int = 0
  short_term_profile: ShortTermProfile = ShortTermProfile()
  current_user_behavior: Optional[List[UserBehavior]] = None
  recommended_places: Set[str] = set()

  def get_redis_key(self):
    return f"user:{self.user_id}:session:{self.session_id}:metadata"

  def __init__(self, **data):
    super().__init__(**data)
    
    if not self.history_key:
      self.history_key = f"user:{self.user_id}:session:{self.session_id}:history"
    if not self.shortlist_key:
      self.shortlist_key = f"user:{self.user_id}:session:{self.session_id}:shortlist"