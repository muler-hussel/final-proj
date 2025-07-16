from pydantic import BaseModel
from typing import Optional, Dict, Literal, List, Set

class TagWeight(BaseModel):
  tag: str
  weight: float
  # Decaying_preferences mentioned consecutivly in 2 sessions, moved into verified_preferences
  # Verified_preferences not mentioned consecutivly in 3 sessions, moved into decaying_preferences
  consecutive_sessions: Optional[int] = None

# Profile according to preferences in one session.
class ShortTermProfile(BaseModel):
  preferences: Dict[str, TagWeight] = {}
  avoids: List[str] = [] 

  # Mongodb does not support set
  @property
  def avoids_set(self) -> Set[str]:
      return set(self.avoids)

  def add_avoids(self, items: List[str]):
      current = set(self.avoids)
      current.update(items)
      self.avoids = list(current)

class LongTermProfile(BaseModel):
  user_id: str
  verified_preferences: Dict[str, TagWeight] = {}
  decaying_preferences: Dict[str, TagWeight] = {}
  avoids: List[str] = []

  @property
  def avoids_set(self) -> Set[str]:
      return set(self.avoids)

  def add_avoids(self, items: List[str]):
      current = set(self.avoids)
      current.update(items)
      self.avoids = list(current)

class UserBehavior(BaseModel):
  place_name: str # Name of place card user acts
  event_type: Literal["click", "view", "shortlist", "unshortlist"]  # Type of behavior
  duration_sec: Optional[float] = 0.0 # Viewing time