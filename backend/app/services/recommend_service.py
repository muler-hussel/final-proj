from pydantic import BaseModel
from typing import List, Any, Optional
from app.db.mongodb import get_database
from app.models.user_preference import UserPreference
from app.models.place_info import PlaceInfo
from app.models.recommend import LongTermProfile, TagWeight, UserBehavior
from app.models.shortlist import ShortlistItem, PlaceReview, PlaceGeo, PlaceDetail, PlaceCard
from app.models.session import SessionState, Message, History
from app.services.shared import language_model, openai_language_model
from app.services.redis_service import redis_service
from app.utils.prompts import (
  EXTRACT_PREFERENCES_PROMPT, 
  RECOMMEND_NEW_PLACES_PROMPT, 
  PLACE_DETAIL_ENRICH_PROMPT,
  CITY_POPULAR_ATTRACTIONS_PROMPT,
  RECOMMEND_POPULAR_PLACES_PROMPT,
)
from langchain_core.output_parsers import JsonOutputParser
import math
import googlemaps
from dotenv import load_dotenv
import os
from datetime import timedelta, datetime
from app.utils.logger import logger
import asyncio

class PlacePreference(BaseModel):
  place: str
  preference: List[str]

class LLMExtract(BaseModel):
  place_preferences: List[PlacePreference]
  avoid: List[str]
  input_preferences: List[str]

class LLMRes(BaseModel):
  content: str
  recommendations: Optional[List[PlaceCard]] = []

# Fields needed in shortlist item
ESSENTIAL_FIELDS = [
  'name', 'types', 'geometry', 'rating', 'website',
  'reviews', 'opening_hours', 'photos', 'price_level', 
  'place_id', 'formatted_address', 'user_ratings_total'
]

ADMINISTRATIVE_TYPES = {
  'administrative_area_level_1',
  'administrative_area_level_2',
  'administrative_area_level_3',
  'political',
  'locality',
  'country',
}

class RecommendService:
  def __init__(self):
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
      | openai_language_model
      | JsonOutputParser(pydantic_object=LLMRes)
    )

    self.enrich_place_detail_chain = (
      PLACE_DETAIL_ENRICH_PROMPT
      | language_model
      | JsonOutputParser()
    )

    self.popular_places_chain = (
      CITY_POPULAR_ATTRACTIONS_PROMPT
      | language_model
      | JsonOutputParser(pydantic_object=PlaceCard)
    )

    self.popular_recommends_chain = (
      RECOMMEND_POPULAR_PLACES_PROMPT
      | openai_language_model
      | JsonOutputParser(pydantic_object=PlaceCard)
    )
    
    self.sigmoid_scale = 0.5

    self.init_weight = 0.8

  async def get_long_preferences(self, user_id: str):
    db = get_database()
    user_preference = UserPreference(db)
    return await user_preference.get_preference(user_id)

  async def save_long_preferences(self, profile: LongTermProfile):
    db = get_database()
    user_preference = UserPreference(db)
    await user_preference.save_preference(profile)

  async def clear_long_preferences(self, user_id: str):
    db = get_database()
    user_preference = UserPreference(db)
    await user_preference.delete_preference(user_id)

  async def update_short_term_profile(self, session_state: SessionState, user_input: str) -> SessionState:
    user_behavior = session_state.current_user_behavior
    place_names = None
    short_term_profile = session_state.short_term_profile
    long_term_profile = await self.get_long_preferences(session_state.user_id)
    # Update shortlist
    if (user_behavior != None): 
      place_names = []
      for behavior in user_behavior:
        place_names.append(behavior.place_name)
        if behavior.event_type == 'shortlist':
          shortlist_place = await redis_service.get_place_info(behavior.place_name)
          if shortlist_place is None:
            shortlist_place = await self.get_place_info(behavior.place_name)
          if shortlist_place is None:
            raise Exception("None")
          await redis_service.add_to_shortlist(session_state, shortlist_place)
        elif behavior.event_type == 'unshortlist':
          await redis_service.remove_from_shortlist(session_state, behavior.place_name)

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

    short_term_profile.add_avoids(extracted_preferences.avoid)
    
    for style in extracted_preferences.input_preferences:
      if style in short_term_profile.preferences:
        cur_weight = short_term_profile.preferences[style].weight
        short_term_profile.preferences[style] = TagWeight(tag=style, weight=(cur_weight + self.init_weight) / 2)
      else:
        short_term_profile.preferences[style] = TagWeight(tag=style, weight=self.init_weight)
    
    shortlist = await redis_service.get_shortlist(session_state.user_id, session_state.session_id)
    session_state = await redis_service.update_session_field(session_state.user_id, session_state.session_id, "shortlist", shortlist)
    return session_state
  
  async def get_place_info(self, place_name: str) -> ShortlistItem | None:
    db = get_database()
    place_info = PlaceInfo(db)
    return await place_info.get_place(place_name)
  
  async def save_place_info(self, placeInfo: ShortlistItem):
    db = get_database()
    place_info = PlaceInfo(db)
    return await place_info.save_place(placeInfo)
  
  async def recommend_places(self, session_state: SessionState, user_input: str):
    user_id = session_state.user_id
    session_id = session_state.session_id
    long_term_profile = await self.get_long_preferences(user_id)
    short_term_profile = session_state.short_term_profile
    recommended_places = session_state.recommended_places
    history = await redis_service.get_simplified_history(session_state)

    raw_data = await self.recommend_places_chain.ainvoke({
      "user_input": user_input,
      "long_term_profile": long_term_profile,
      "short_term_profile": short_term_profile,
      "recommended_places": recommended_places,
      "history": history,
    })

    raw_popular = await self.popular_recommends_chain.ainvoke({
      "user_input": user_input,
      "recommended_places": recommended_places,
      "history": history,
    })

    # logger.info(f"short_term_profile: {short_term_profile}, user_input: {user_input}, recommend_places: {raw_data}")
    
    result = LLMRes(**raw_data)
    recommendations = result.recommendations
    response = Message(
      content=result.content
    )

    populars = [PlaceCard(**p) for p in raw_popular]

    for place in recommendations:
      # If place information is in DB, get place info, else fetch from google map api
      session_state.add_recommended_places(place.name)
      place_info = await self.get_or_fetch_place_brief(place.name, place.description, place.recommend_reason)
      if place_info:
        response.recommendations.append(place_info)
    
    for place in populars:
      # If place information is in DB, get place info, else fetch from google map api
      session_state.add_recommended_places(place.name)
      place_info = await self.get_or_fetch_place_brief(place.name, place.description, place.recommend_reason)
      if place_info:
        response.populars.append(place_info)
    
    user_history_entry = History(
      role="ai",
      message=response
    )
    await redis_service.append_history(session_state, user_history_entry)
    await redis_service.save_session_state(session_state)

    return response
  
  async def get_or_fetch_place_brief(self, place_name: str, description: Optional[str] = None, recommend_reason: Optional[str] = None) -> ShortlistItem:
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
        if not place_info:
          result = self.gmaps.place(place_id, ESSENTIAL_FIELDS).get("result")
          place_info = self.google_to_shortlist(result, description, recommend_reason)
    if place_info: 
      place_info.description = description
      place_info.info.recommend_reason = recommend_reason
      # Save in Redis and MongoDB
      await redis_service.save_place_info(place_info.name, place_info)
      await self.save_place_info(place_info)
      asyncio.create_task(self.enrich_place_detail(place_info.name))
    
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
      total_ratings=result.get('user_ratings_total', None),
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

  # Place information needs to be generated by ai or updated
  async def enrich_place_detail(self, place_name: str) -> ShortlistItem:
    # Redis lock ensures tasks not duplicate
    lock_key = f"place_lock:{place_name}"
    if redis_service.get(lock_key):
      return
    try:
      redis_service.set(lock_key, "1", ex=300)
      place = await redis_service.get_place_info(place_name)

      if not place:
        place = await self.get_place_info(place_name)
      if not place:
        place = await self.get_or_fetch_place_brief(place_name, None, None)
      
      if not place:
        return

      isChanged = False
      # City: Top ten attractions in city
      if (place.type == "city") and (len(place.sub_items) == 0):
        raw_data = await self.popular_places_chain.ainvoke(place_name)
        popular_places: List[PlaceCard] = [PlaceCard(**item) for item in raw_data]
        for p in popular_places:
          place_info = await self.get_or_fetch_place_brief(p.name, p.description, p.recommend_reason)
          if (place_info):
            place.sub_items.append(place_info)
        isChanged = True

      # Not city: update if over one month or haven't generated by ai
      elif (place.type != "city") and ((place.info.advice_trip is None) or (datetime.now() - place.updated_time > timedelta(days=30))):
        enrich_data = await self.enrich_place_detail_chain.ainvoke(place_name)
        place.info.pros = enrich_data['pros']
        place.info.cons = enrich_data['cons']
        place.info.advice_trip = enrich_data['advice_trip']
        isChanged = True
      
      if isChanged:
        place.updated_time = datetime.now()
        await redis_service.save_place_info(place_name, place)
        await self.save_place_info(place)

      return place

    finally:
      redis_service.delete(lock_key)

recommend_service = RecommendService()