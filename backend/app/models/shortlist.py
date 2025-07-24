from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import datetime

# Geometry info of place
class PlaceGeo(BaseModel):
  location: List[float] # lat, lng
  viewport: List[List[float]] # northeast lat & lng, southwest lat & lng

  @field_validator('location')
  def validate_location(cls, v):
    if len(v) != 2:
      raise ValueError("location should contain [lat, lng]")
    return v
    
  @field_validator('viewport')
  def validate_viewport(cls, v):
    if len(v) != 2 or any(len(point) != 2 for point in v):
      raise ValueError("viewport should contain [lat, lng]")
    return v

# Reviews extract by ai
class PlaceReview(BaseModel):
  review: str
  type: int # 0-Google latest, 1-Google relevant, 2-TripAdvisor latest, 3-TripAdivsor detailed

class PlaceCard(BaseModel):
  name: str
  description: Optional[str] = None
  recommend_reason: Optional[str] = None

# Infomation shown in drawer
class PlaceDetail(BaseModel):
  recommend_reason: Optional[str] = None # Recommend reason, city & attraction
  website: Optional[str] = None # Official website, if is attraction
  address: Optional[str] = None
  weekday_text: Optional[List[str]] = None
  rating: Optional[float] = None
  reviews: Optional[List[PlaceReview]] = None # extract by AI
  pros: Optional[List[str]] = None
  cons: Optional[List[str]] = None
  advice_trip: Optional[str] = None # Adviced by ai
  prices: Optional[List[str]] = None # extract from official website by ai
  price_level: Optional[int] = None
  total_ratings: Optional[int] = None
  
# Cities, attractions user like
class ShortlistItem(BaseModel):
  name: str
  type: Optional[str] = None # 'city' | 'attraction'
  place_id: Optional[str] = None
  description: Optional[str] = None
  tags: Optional[List[str]] = [] # tags of attraction, 'museum', 'animal', 'history'
  info: Optional[PlaceDetail] = None
  sub_items: Optional[List["ShortlistItem"]] = [] # If city, containing recommended attraction names of this city
  geometry: Optional[PlaceGeo] = None
  status: Optional[str] = "pending"  # Backend asynchronous processing status 'pending', 'processing', 'ready', 'error'
  photos: Optional[List[str]] = None
  updated_time: Optional[datetime] = None # Check website, weekday_text, prices, reviews every month

  class Config:
    arbitrary_types_allowed = True
    from_attributes = True

ShortlistItem.model_rebuild()