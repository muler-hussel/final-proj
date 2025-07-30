from datetime import datetime, timedelta
import json
import re
from typing import List
from app.utils.prompts import CREATE_ITINERARY_PROMPT
from app.services.shared import openai_language_model, language_model
from app.models.session import DailyItinerary, Message, SessionState, History
from app.services.redis_service import redis_service
from langchain.agents import initialize_agent
from langchain.agents.agent_types import AgentType
from app.services.recommend_service import recommend_service
from app.utils.tools import get_route_info
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.output_parsers import JsonOutputParser

class ItineraryService:
  def __init__(self):
    # self.llm_with_tools = language_model.bind_tools([get_route_info])
    # self.agent = initialize_agent(
    #   tools=[get_route_info],
    #   llm=openai_language_model,
    #   agent=AgentType.OPENAI_MULTI_FUNCTIONS,
    #   verbose=True
    # )
    self.create_itinerary_chain=(
      CREATE_ITINERARY_PROMPT
      | language_model
      | JsonOutputParser()
    )
  
  async def create_itinerary(self, session_state: SessionState, user_input: str):
    history_str = await redis_service.get_simplified_history(session_state)
    shortlist = await redis_service.get_shortlist(session_state.user_id, session_state.session_id)
    place_names = ",".join(f"{s.name}: {s.info.weekday_text}" for s in shortlist)
    
    # user_prompt = CREATE_ITINERARY_PROMPT.format(
    #   user_input=user_input,
    #   history=history_str,
    #   place_names=place_names
    # )
    # messages = [HumanMessage(user_prompt)]
    # while True:
    #   ai_msg = self.llm_with_tools.invoke(messages)
    #   messages.append(ai_msg)

    #   if not getattr(ai_msg, "tool_calls", None):
    #     break

    #   for tool_call in ai_msg.tool_calls:
    #     tool_name = tool_call["name"]
    #     args = tool_call["args"]
    #     if isinstance(args, str):
    #       args = json.loads(args)

    #     tool_fn = {
    #       "get_route_info": get_route_info
    #     }.get(tool_name)

    #     if tool_fn is None:
    #       raise ValueError(f"No tool found for: {tool_name}")

    #     tool_output = tool_fn.invoke(args)

    #     messages.append(
    #       ToolMessage(content=tool_output, tool_call_id=tool_call["id"])
    #     )

    # raw_data = ai_msg.content
    # print(raw_data)
    # json_str = re.sub(r"^```json|```$", "", raw_data.strip(), flags=re.MULTILINE).strip()
    # parsed_data = json.loads(json_str)
    # response = Message(**parsed_data)

    raw_data = await self.create_itinerary_chain.ainvoke({
      "user_input":user_input,
      "history":history_str,
      "place_names":place_names
    })

    response = Message(**raw_data)

    shortlist_names = set(s.name for s in shortlist)
    if not response.itinerary:
      return response
    
    itinerary = response.itinerary
    for i in range(len(itinerary)):
      if itinerary[i].type == 'visit':
        place_name = itinerary[i].place_name
        # If recommend more places
        if place_name and (place_name != "null") and (place_name not in shortlist_names):
          place_info = await recommend_service.get_or_fetch_place_brief(place_name, None, None)
          response.recommendations.append(place_info)
    
    itinerary = await self.update_itinerary_time(itinerary)
    
    user_history_entry = History(
      role="ai",
      message=response
    )
    await redis_service.append_history(session_state, user_history_entry)
    return response
  
  async def update_itinerary_time(self, itinerary: List[DailyItinerary]) -> List[DailyItinerary]:
    sorted_itinerary = sorted(
      itinerary,
      key=lambda x: (
        x.date,
        int(x.start_time.split(":")[0]) * 60 + int(x.start_time.split(":")[1])
      )
    )
    for i in range(1, len(sorted_itinerary) - 1):
      if sorted_itinerary[i].type == 'commute':
        commute_mode = sorted_itinerary[i].commute_mode
        if 'WALK' in commute_mode.upper():
          commute_mode = 'WALK'
        elif 'TRANSIT' in commute_mode.upper():
          commute_mode = 'TRANSIT'
        elif 'DRIV' in commute_mode.upper():
          commute_mode = 'DRIVE'
        elif 'BICYCL' in commute_mode.upper():
          commute_mode = 'BICYCLE'
        sorted_itinerary[i].commute_mode = commute_mode
        arrival_time = sorted_itinerary[i+1].start_time
        origin = sorted_itinerary[i-1].place_name
        destination = sorted_itinerary[i+1].place_name

        today = datetime.now().date()
        hours, minutes = map(int, arrival_time.split(':'))
        utc_dt = datetime.combine(today, datetime.min.time()) + timedelta(hours=hours, minutes=minutes)
        duration, mode, route_steps = await get_route_info(origin, destination, commute_mode, utc_dt.isoformat(timespec='seconds') + 'Z')
        if not duration:
          print("Fail to get route")
          continue
        
        if len(route_steps) > 1:
          # arrival = route_steps[len(route_steps) - 1].arrival_time
          # sorted_itinerary[i].end_time = self._rfc_to_hhmm(arrival)

          for step in route_steps:
            if step.departure_time:
              step.departure_time = self._rfc_to_hhmm(step.departure_time)
              step.arrival_time = self._rfc_to_hhmm(step.arrival_time)
          sorted_itinerary[i].route_steps = route_steps
        
        arrival_dt = datetime.strptime(sorted_itinerary[i].end_time, "%H:%M")
        duration_seconds = float(duration[:-1])
        departure_dt = arrival_dt - timedelta(seconds=duration_seconds)
        sorted_itinerary[i].start_time = departure_dt.strftime("%H:%M")
        sorted_itinerary[i].commute_mode = mode

    return sorted_itinerary
  
  def _rfc_to_hhmm(self, time: str) -> str:
    time_dt = datetime.fromisoformat(time.replace("Z", "+00:00"))
    return time_dt.strftime("%H:%M")

itinerary_service = ItineraryService()