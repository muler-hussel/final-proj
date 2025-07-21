from langchain.tools import tool
from pydantic import BaseModel, Field
from enum import Enum
from app.db.mongodb import get_database
from app.models.place_info import PlaceInfo
import googlemaps
from dotenv import load_dotenv
import os

class TravelMode(str, Enum):
  driving = "driving"
  walking = "walking"
  bicycling = "bicycling"
  transit = "transit"

class RouteInput(BaseModel):
  origin: str = Field(..., description="Starting location")
  destination: str = Field(..., description="Ending location")
  mode: TravelMode = Field(..., description="Travel mode: one of 'driving', 'walking', 'bicycling', or 'transit'")

load_dotenv()
key = os.getenv("GOOGLE_API")
gmaps = googlemaps.Client(key=key)

# Should be out of a class
@tool(args_schema=RouteInput)
async def get_route_info(params: RouteInput) -> str:
  """
  Use Google Maps to get travel time and distance.
  
  Args:
      origin (str): Starting location.
      destination (str): Destination location.
      mode (str): Travel mode. Must be one of ["driving", "walking", "bicycling", "transit"].
  """

  origin = params.origin
  destination = params.destination
  mode = params.mode or "transit"

  db = await get_database()
  origin_id = (await PlaceInfo(db).get_place(origin)).place_id
  destination_id = (await PlaceInfo(db).get_place(destination)).place_id

  try: 
    res = gmaps.directions('place_id:'+origin_id, 'place_id:'+destination_id, mode=mode)
    if not res or not isinstance(res, list) or len(res) == 0:
      return "No route info found."
    first_route = res[0]
    legs = first_route.get('legs', [])
    if not legs:
      return "Route info not valid"
    duration = legs[0].get('duration', {}).get('text', '')
    print(duration)
    return duration
  except Exception as e:
    print(f"Error get duration from {origin} to {destination}: {e}")
    return ''
