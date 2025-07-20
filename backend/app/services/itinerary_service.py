from app.utils.prompts import CREATE_ITINERARY_PROMPT
from app.services.shared import language_model
from app.models.session import Message, SessionState, History
from app.services.redis_service import redis_service
from langchain.tools import tool
from langchain.agents import initialize_agent
from langchain.agents.agent_types import AgentType
from pydantic import BaseModel, Field
from enum import Enum
from app.db.mongodb import get_database
from app.models.place_info import PlaceInfo
import googlemaps
from dotenv import load_dotenv
import os
from app.services.recommend_service import RecommendService

class TravelMode(str, Enum):
    driving = "driving"
    walking = "walking"
    bicycling = "bicycling"
    transit = "transit"

class RouteInput(BaseModel):
    origin: str = Field(..., description="Starting location")
    destination: str = Field(..., description="Ending location")
    mode: TravelMode = Field(..., description="Travel mode: one of 'driving', 'walking', 'bicycling', or 'transit'")

class ItineraryService:
  def __init__(self):
    self.tools = [self.get_route_info]

    self.agent = initialize_agent(
      tools=self.tools,
      llm=language_model,
      agent=AgentType.OPENAI_FUNCTIONS,
      verbose=True
    )

    load_dotenv()
    self.key = os.getenv("GOOGLE_API")
    self.gmaps = googlemaps.Client(key=self.key)
  
  async def create_itinerary(self, session_state: SessionState, user_input: str):
    history = (await redis_service.get_history(session_state.user_id, session_state.session_id))[-10:]
    history_str = "\n".join(f"{msg.role}: {msg.message}" for msg in history)
    shortlist = await redis_service.get_shortlist(session_state)
    place_names = ",".join(f"{s.name}: {s.info.weekday_text}" for s in shortlist)
    
    user_prompt = CREATE_ITINERARY_PROMPT.format(
      user_input=user_input,
      history=history_str,
      place_names=place_names
    )
    raw_data = await self.agent.ainvoke(user_prompt)
    response = Message.model_validate_json(raw_data)

    shortlist_names = set(s.name for s in shortlist)
    # If recommend more places
    for place in response.itinerary:
      db = await get_database()
      place_name = place.place_name
      if place_name not in shortlist_names:
        place_info = await RecommendService(db).get_or_fetch_place_brief(place_name, None, None)
        response.recommendations.append(place_info)
    
    user_history_entry = History(
      role="ai",
      message=response
    )
    await redis_service.append_history(session_state, user_history_entry)
    return response

  @tool(args_schema=RouteInput)
  async def get_route_info(self, origin: str, destination: str, mode: str = "transit") -> str:
    """
    Use Google Maps to get travel time and distance.
    
    Args:
        origin (str): Starting location.
        destination (str): Destination location.
        mode (str): Travel mode. Must be one of ["driving", "walking", "bicycling", "transit"].
    """
    db = await get_database()
    origin_id = (await PlaceInfo(db).get_place(origin)).place_id
    destination_id = (await PlaceInfo(db).get_place(destination)).place_id

    try: 
      res = self.gmaps.directions('place_id:'+origin_id, 'place_id:'+destination_id, mode)
      duration = res.get('routes').get('legs')[0].get('duration')
      return duration
    except Exception as e:
      print(f"Error get duration from {origin} to {destination}: {e}")
      return None
    

itinerary_service = ItineraryService()