from pydantic import BaseModel
from typing import List, Any, Dict, Optional
from app.db.mongodb import MongoDB
from app.models.user_preference import UserPreference
from app.models.place_info import PlaceInfo
from app.models.recommend import LongTermProfile, TagWeight, UserBehavior
from app.models.shortlist import ShortlistItem, PlaceReview, PlaceGeo, PlaceDetail
from app.models.session import SessionState
from app.services.shared import language_model
from app.services.redis_service import redis_service
from app.utils.prompts import EXTRACT_PREFERENCES_PROMPT, RECOMMEND_NEW_PLACES_PROMPT
from langchain_core.output_parsers import JsonOutputParser
import math
import googlemaps
from dotenv import load_dotenv
import os
from datetime import timedelta, datetime
from app.utils.logger import logger

class PlacePreference(BaseModel):
  place: str
  preference: List[str]

class LLMExtract(BaseModel):
  place_preferences: List[PlacePreference]
  avoid: List[str]
  input_preferences: List[str]

class RecommendationItem(BaseModel):
  place_name: str
  description: str
  recommend_reason: str

class LLMRecommend(BaseModel):
  content: str
  recommendations: List[RecommendationItem]

class LLMResponse(BaseModel):
  content: Optional[str] = None
  recommendations: Optional[List[ShortlistItem]] = [] 

# Fields needed in shortlist item
ESSENTIAL_FIELDS = [
  'name', 'types', 'geometry', 'rating', 'website',
  'reviews', 'opening_hours', 'photos', 'price_level', 
  'place_id', 'formatted_address'
]

ADMINISTRATIVE_TYPES = {
  'administrative_area_level_1',
  'administrative_area_level_2',
  'administrative_area_level_3',
  'administrative_area_level_4',
  'administrative_area_level_5',
  'political',
}

class RecommendService:
  def __init__(self, mongodb: MongoDB):
    self.user_preference = UserPreference(mongodb.db)
    self.place_info = PlaceInfo(mongodb.db)

    load_dotenv()
    self.key = os.getenv("GOOGLE_API")
    self.gmaps = googlemaps.Client(key=self.key)

    self.extract_preferences_chain = (
      EXTRACT_PREFERENCES_PROMPT
      | language_model
      | JsonOutputParser()
    )

    self.recommend_places_chain = (
      RECOMMEND_NEW_PLACES_PROMPT
      | language_model
      | JsonOutputParser()
    )

    self.sigmoid_scale = 0.5

    self.init_weight = 0.8

  async def get_long_preferences(self, user_id: str):
    return await self.user_preference.get_preference(user_id)

  async def save_long_preferences(self, profile: LongTermProfile):
    await self.user_preference.save_preference(profile)

  async def clear_long_preferences(self, user_id: str):
    await self.user_preference.delete_preference(user_id)

  async def update_short_term_profile(self, session_state: SessionState, user_input: str) -> SessionState:
    user_behavior = session_state.current_user_behavior
    place_names = None
    short_term_profile = session_state.short_term_profile
    long_term_profile = await self.get_long_preferences(session_state.user_id)

    if (user_behavior != None): 
      place_names = list({behavior.place_name for behavior in user_behavior})

    raw_data = await self.extract_preferences_chain.ainvoke({
      "places": place_names, 
      "user_input": user_input,
      "short_term_profile": short_term_profile,
      "long_term_profile": long_term_profile,
    })
    # logger.info(f"places: {place_names}, user_input: {user_input}, extracted_preferences: {raw_data}")
    extracted_preferences = LLMExtract(**raw_data)

    for item in extracted_preferences.place_preferences:
      place_name = item.place
      inferred_styles = item.preference

      # Behaviors acted at each place according to user_behavior
      if user_behavior != None:
        place_behaviors = [b for b in user_behavior if b.place_name == place_name]

        # Total weight of each place, according to place_behaviors
        total_weight = self.sigmoid(sum(self.raw_behavior_score(b) for b in place_behaviors))

        # Add new weight to short_term_profile, according to each style
        for style in inferred_styles:
          if style in short_term_profile.preferences:
            cur_weight = short_term_profile.preferences[style].weight
            new_weight = (cur_weight + total_weight) / 2
            short_term_profile.preferences[style] = TagWeight(tag=style, weight=min(1.0, max(0.0, new_weight)))
          else:
            short_term_profile.preferences[style] = TagWeight(tag=style, weight=total_weight)
      else:
        for style in inferred_styles:
          short_term_profile.preferences[style] = TagWeight(tag=style, weight=self.init_weight)

    for item in extracted_preferences.avoid:
      short_term_profile.avoids.add(item)
    
    for style in extracted_preferences.input_preferences:
      if style in short_term_profile.preferences:
        cur_weight = short_term_profile.preferences[style].weight
        short_term_profile.preferences[style] = TagWeight(tag=style, weight=(cur_weight + self.init_weight) / 2)
      else:
        short_term_profile.preferences[style] = TagWeight(tag=style, weight=self.init_weight)
    print(short_term_profile)
    await redis_service.save_session_state(session_state)
    return session_state
  
  async def get_place_info(self, place_name: str) -> ShortlistItem | None:
    return await self.place_info.get_place(place_name)
  
  async def sava_place_info(self, placeInfo: ShortlistItem):
    return await self.place_info.save_place(placeInfo)
  
  async def recommend_places(self, session_state: SessionState, user_input: str):
    user_id = session_state.user_id
    session_id = session_state.session_id
    long_term_profile = await self.get_long_preferences(user_id)
    short_term_profile = session_state.short_term_profile
    recommended_places = session_state.recommended_places
    history = (await redis_service.get_history(user_id, session_id))[-10:] # recent 10 conversation
    history_str = "\n".join(f"{msg['role']}: {msg['message']}" for msg in history)

    raw_data = await self.recommend_places_chain.ainvoke({
      "user_input": user_input,
      "long_term_profile": long_term_profile,
      "short_term_profile": short_term_profile,
      "recommended_places": recommended_places,
      "history": history_str,
    })
    # logger.info(f"short_term_profile: {short_term_profile}, user_input: {user_input}, recommend_places: {raw_data}")
    result = LLMRecommend(**raw_data)
    await redis_service.append_history(session_state, raw_data, "ai")

    recommendations = result.recommendations
    response = LLMResponse()
    response.content = result.content
    
    for place in recommendations:
      # If place information is in DB, get place info, else fetch from google map api
      session_state.recommended_places.add(place.place_name)
      place_info = await self.get_or_fetch_place_brief(place.place_name, place.description, place.recommend_reason)
      # TODO:Check if need updating
      response.recommendations.append(place_info) 
      
    await redis_service.save_session_state(session_state)
    return response
  
  async def get_or_fetch_place_brief(self, place_name: str, description: str, recommend_reason: str) -> ShortlistItem:
    # Check if in Redis
      place_info = await redis_service.get_place_info(place_name)
      # Check if in MongoDB
      if place_info is None:
        place_info = await self.get_place_info(place_name)
      if place_info is None:
        # Fetch from google map api
        places = self.gmaps.find_place(place_name, "textquery", fields=['place_id', 'name']).get("candidates", [])
        if len(places):
          place_id = places[0].get('place_id')
          official_name = places[0].get('name')
          place_info = await self.get_place_info(official_name)
          if place_info:
            return place_info
          result = self.gmaps.place(place_id, ESSENTIAL_FIELDS).get("result")
          place_info = self.google_to_shortlist(result, description, recommend_reason)

          # Save in Redis and MongoDB
          await redis_service.save_place_info(place_info.name, place_info)
          await self.sava_place_info(place_info)
      return place_info

  def raw_behavior_score(self, behavior: UserBehavior) -> float:
    return (
      0.5 * (behavior.event_type == "click") +
      1.0 * (behavior.event_type == "view") +
      3.0 * (behavior.event_type == "shortlist") -
      3.0 * (behavior.event_type == "unshortlist") +
      0.1 * (behavior.duration_sec / 10 if behavior.duration_sec else 0)
    )
  
  def sigmoid(self, x: float) -> float:
    return 1 / (1 + math.exp(-self.sigmoid_scale * x))
  
  def google_to_placeinfo(self, result: Any, recommend_reason: str) -> PlaceDetail:
    opening_hours = result.get('opening_hours', {})
    reviews = result.get('reviews', [])
    
    return PlaceDetail(
      recommend_reason=recommend_reason,
      website=result.get('website', None),
      address=result.get('formatted_address', None),
      weekday_text=opening_hours.get('weekday_text', []),
      rating=result.get('rating', None),
      reviews=[PlaceReview(
        review=r.get('text', ''),
        type=1,
      ) for r in reviews if isinstance(r, dict)],
      price_level=result.get('price_level', None),
    )

  def google_to_shortlist(self, result: Any, description: str, recommend_reason: str) -> ShortlistItem:
    photos = result.get('photos', [])
    type = "city" if ADMINISTRATIVE_TYPES.intersection(result.get('types', [])) else "attraction"
    google_geom = result.get('geometry', {})

    return ShortlistItem(
      name=result.get('name'),
      type=type,
      place_id=result.get('place_id'),
      description=description,
      info=self.google_to_placeinfo(result, recommend_reason),
      geometry=PlaceGeo(
        location=[google_geom.get('location').get('lat'), google_geom.get('location').get('lng')],
        viewport=[
          [google_geom.get('viewport').get('northeast').get('lat'), 
          google_geom.get('viewport').get('northeast').get('lng')],
          [google_geom.get('viewport').get('southwest').get('lat'),
          google_geom.get('viewport').get('southwest').get('lng')]
        ]
      ),
      photos=[(f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=1600&photo_reference={p.get('photo_reference')}&key={self.key}")
        for p in photos if p.get('photo_reference')],
      updated_time=datetime.now()
    )

  # TODO:Place information needs to be generated by ai, double checked or updated
  # async def enrich_place_detail(self, place_name: str):
  #   place = await self.get_place_info(place_name)
  #   if not place:
  #     return

  #   # TODO:City: attractions in city
  #   if place.type == "city":
  #     place.sub_items.append('1')

  #   # Not city: update if over one month
  #   elif (place.info.summarized_review is None) or (datetime.now() - place.updated_time > timedelta(days=30)):
  #     fresh_data = await fetch_fresh_google_data(name)
  #     place.website = fresh_data.get("website")
  #     place.weekday_text = fresh_data.get("weekday_text")

  #     # 检查官网 weekday & prices
  #     extra = await check_official_site_info(place.website)
  #     place.prices = extra.get("prices")
  #     place.weekday_text = extra.get("weekday_text") or place.weekday_text

  #     # 获取评论并总结
  #     reviews = await get_recent_reviews(name)
  #     place.reviews = reviews
  #     place.summarized_review = await summarize_reviews(reviews)

  #     place.updated_time = datetime.now()

  #   await save_to_db(place)