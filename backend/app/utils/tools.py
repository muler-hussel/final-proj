from datetime import datetime
import json
from typing import List, Literal, Optional, Tuple
from langchain.tools import tool
from pydantic import BaseModel, Field, field_validator
from enum import Enum
from dotenv import load_dotenv
import os
from app.db.mongodb import get_database
import requests
from app.models.session import RouteStep
from app.models.place_info import PlaceInfo

class TravelMode(str, Enum):
  driving = "driving"
  walking = "walking"
  bicycling = "bicycling"
  transit = "transit"

class RouteInput(BaseModel):
  origin: str = Field(..., description="Starting location")
  destination: str = Field(..., description="Ending location")
  mode: TravelMode = Field(..., description="Travel mode: one of 'driving', 'walking', 'bicycling', or 'transit'")
  arrival_time: Optional[str] = Field(None, description="Optional arrival time in RFC 3339 format (e.g., '2024-05-20T14:30:00Z'). "),

  @field_validator("arrival_time")
  def validate_arrival_time(cls, v):
    if v is not None:
      try:
        datetime.fromisoformat(v.replace("Z", "+00:00"))
      except ValueError:
        raise ValueError("arrival_time must be in RFC 3339 format (e.g., '2024-05-20T14:30:00Z')")
    return v


load_dotenv()
key = os.getenv("GOOGLE_API")

# Should be out of a class
# @tool
async def get_route_info(origin: str, destination: str, mode: Literal["WALK", "TRANSIT", "BICYCLE", "DRIVE"],  arrival_time: Optional[str] = None) -> Optional[Tuple[str, str, List[RouteStep]]]:
  """
  Use Google Maps to get travel time and distance.
  
  Input route data with fields:
    - origin (str): Starting location.
    - destination (str): Destination location.
    - mode (str): Travel mode. Must be one of ["WALK", "TRANSIT", "BICYCLE", "DRIVE"].
    - arrival_time (Optional[str]): Arrival time in RFC 3339 format (e.g., '2024-05-20T14:30:00Z'). Only used if mode is 'transit'.
  """

  url = f"https://routes.googleapis.com/directions/v2:computeRoutes"

  headers = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": key,
    "X-Goog-FieldMask": "routes.duration,routes.legs"
  }

  db = get_database()
  origin_id = (await PlaceInfo(db).get_place(origin)).place_id
  destination_id = (await PlaceInfo(db).get_place(destination)).place_id
  body = {
    "origin": { "placeId": origin_id },
    "destination": { "placeId": destination_id },
    "travelMode": mode.upper(),
    "arrivalTime": arrival_time
  }
  response = requests.post(url, headers=headers, data=json.dumps(body))
  if response.status_code == 200:
    data = response.json()
    if not data and mode.upper() != 'WALK':
      new_body = {
        "origin": { "placeId": origin_id },
        "destination": { "placeId": destination_id },
        "travelMode": 'WALK',
      }
      print("turn to walk")
      response = requests.post(url, headers=headers, data=json.dumps(new_body))
      data = response.json()
      mode = 'WALK'
    if data and mode.upper() == 'WALK': 
      duration = float(data["routes"][0]["duration"][:-1])
      if duration > 3600:
        new_body = {
          "origin": { "placeId": origin_id },
          "destination": { "placeId": destination_id },
          "travelMode": 'DRIVE',
          "arrivalTime": arrival_time
        }
        print("turn to drive")
        response = requests.post(url, headers=headers, data=json.dumps(new_body))
        data = response.json()
        mode = 'DRIVE'
    if not data:
      print("Error:", response.status_code, response.text)
      return None, None, None
    duration = data["routes"][0]["duration"]
    steps = data["routes"][0]["legs"][0]["steps"]
    
    route_steps = []
    if mode == 'TRANSIT':
      steps_overview = data["routes"][0]["legs"][0]["stepsOverview"]["multiModalSegments"]
      for l in steps_overview:
        step_mode = l.get('travelMode', '')
        step_start = l.get("stepStartIndex")
        step_end = l.get("stepEndIndex")
        step_duration = 0
        for i in range(step_start, step_end + 1):
          step_duration += float(steps[i]["staticDuration"][:-1])
        if step_mode == 'TRANSIT':
          route_steps.append(RouteStep(
            step_mode=step_mode,
            step_duration=_format_duration(step_duration),
            departure_stop=steps[step_start].get("transitDetails", {}).get("stopDetails", {}).get("departureStop", {}).get("name", ""),
            departure_time=steps[step_start].get("transitDetails", {}).get("stopDetails", {}).get("departureTime", ""),
            arrival_stop=steps[step_end].get("transitDetails", {}).get("stopDetails", {}).get("arrivalStop", {}).get("name", ""),
            arrival_time=steps[step_end].get("transitDetails", {}).get("stopDetails", {}).get("arrivalTime", ""),
            transit_name = steps[step_start].get("transitDetails", {}).get("transitLine", {}).get("name", ""),
            color=steps[step_start].get("transitDetails", {}).get("transitLine", {}).get("color", ""),
          ))
        else:
          route_steps.append(RouteStep(
            step_mode=step_mode,
            step_duration=_format_duration(step_duration),
          ))
    return duration, mode, route_steps
  else:
    print("Error:", response.status_code, response.text)
    return None, None, None

def _format_duration(duration):
  hours = int(duration // 3600)
  minutes = int((duration % 3600) // 60)
  remaining_seconds = duration % 60
  
  parts = []
  if hours > 0:
    parts.append(f"{hours} Hours")
  if minutes > 0:
    parts.append(f"{minutes} Minutes")
  if len(parts) == 0:
    parts.append(f"{remaining_seconds:.0f} Seconds")
  
  return " ".join(parts)