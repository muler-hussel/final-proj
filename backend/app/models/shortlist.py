from pydantic import BaseModel
from typing import List, Optional, Dict, Literal
from datetime import datetime

# Geometry info of place
class PlaceGeo(BaseModel):
  location: List[float] # lat, lng
  viewport: List[List[float]] # northeast lat & lng, southwest lat & lng

# Images retrieved from Google Map, city & attraction
class PlacePhoto(BaseModel):
  height: int
  width: int
  html_attributions: Optional[List[str]] = None
  photo_reference: str

# Reviews extract by ai
class PlaceReview(BaseModel):
  review: str
  type: int # 0-Google latest, 1-Google relevant, 2-TripAdvisor latest, 3-TripAdivsor detailed
  
# Infomation shown in drawer
class PlaceInfo(BaseModel):
  photos: Optional[List[PlacePhoto]] = None
  description: Optional[str] = None # Recommend reason, city & attraction
  website: Optional[str] = None # Official website, if is attraction
  address: Optional[str] = None
  weekday_text: Optional[List[str]] = None
  rating: Optional[float] = None
  reviews: Optional[List[PlaceReview]] = None # extract by AI
  review_updated: Optional[datetime] # Updated every month
  pros: Optional[List[str]] = None
  contra: Optional[List[str]] = None
  summarized_review: Optional[str] # Summarized according to reviews
  prices: Optional[List[str]] = None # extract from official website by ai
  
# Cities, attractions user like
class ShortlistItem(BaseModel):
  name: str
  type: str # 'city' | 'attraction'
  place_id: str
  city: Optional[str] = None # If attraction, belongs to which city
  tags: Optional[List[str]] = [] # tags of attraction, 'museum', 'animal', 'history'
  info: Optional[PlaceInfo] = None
  sub_items: Optional[List[str]] = [] # If city, containing recommended attraction ids of this city
  geometry: Optional[PlaceGeo] = PlaceGeo()

  class Config:
    arbitrary_types_allowed = True
    from_attributes = True

ShortlistItem.model_rebuild()