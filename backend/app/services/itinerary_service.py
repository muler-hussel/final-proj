import json
import re
from app.utils.prompts import CREATE_ITINERARY_PROMPT
from app.services.shared import language_model
from app.models.session import Message, SessionState, History
from app.services.redis_service import redis_service
from langchain.agents import initialize_agent
from langchain.agents.agent_types import AgentType
from pydantic import BaseModel, Field
from enum import Enum
from app.db.mongodb import get_database
from app.services.recommend_service import RecommendService
from app.utils.tools import get_route_info

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
    self.agent = initialize_agent(
      tools=[get_route_info],
      llm=language_model,
      agent=AgentType.OPENAI_FUNCTIONS,
      verbose=True
    )
  
  async def create_itinerary(self, session_state: SessionState, user_input: str):
    history = (await redis_service.get_history(session_state.user_id, session_state.session_id))[-10:]
    history_str = "\n".join(f"{msg.role}: {msg.message}" for msg in history)
    shortlist = await redis_service.get_shortlist(session_state.user_id, session_state.session_id)
    place_names = ",".join(f"{s.name}: {s.info.weekday_text}" for s in shortlist)
    
    user_prompt = CREATE_ITINERARY_PROMPT.format(
      user_input=user_input,
      history=history_str,
      place_names=place_names
    )
    raw_data = await self.agent.ainvoke(user_prompt)
    output_str = raw_data["output"]
    json_str = re.sub(r"^```json|```$", "", output_str.strip(), flags=re.MULTILINE).strip()
    parsed_data = json.loads(json_str)
    response = Message(**parsed_data)

    shortlist_names = set(s.name for s in shortlist)
    # If recommend more places
    for place in response.itinerary:
      db = await get_database()
      place_name = place.place_name
      if place_name and (place_name != "null") and (place_name not in shortlist_names):
        place_info = await RecommendService(db).get_or_fetch_place_brief(place_name, None, None)
        response.recommendations.append(place_info)
    
    user_history_entry = History(
      role="ai",
      message=response
    )
    await redis_service.append_history(session_state, user_history_entry)
    return response

itinerary_service = ItineraryService()