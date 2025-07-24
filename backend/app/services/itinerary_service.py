import json
import re
from app.utils.prompts import CREATE_ITINERARY_PROMPT
from app.services.shared import openai_language_model, language_model
from app.models.session import Message, SessionState, History
from app.services.redis_service import redis_service
from langchain.agents import initialize_agent
from langchain.agents.agent_types import AgentType
from app.db.mongodb import get_database
from app.services.recommend_service import RecommendService
from app.utils.tools import get_route_info
from langchain_core.messages import HumanMessage, ToolMessage

class ItineraryService:
  def __init__(self):
    self.llm_with_tools = language_model.bind_tools(tools=[get_route_info])
    self.agent = initialize_agent(
      tools=[get_route_info],
      llm=openai_language_model,
      agent=AgentType.OPENAI_MULTI_FUNCTIONS,
      verbose=True
    )
  
  async def create_itinerary(self, session_state: SessionState, user_input: str):
    history_str = await redis_service.get_simplified_history(session_state)
    shortlist = await redis_service.get_shortlist(session_state.user_id, session_state.session_id)
    place_names = ",".join(f"{s.name}: {s.info.weekday_text}" for s in shortlist)
    
    user_prompt = CREATE_ITINERARY_PROMPT.format(
      user_input=user_input,
      history=history_str,
      place_names=place_names
    )
    messages = [HumanMessage(user_prompt)]
    while True:
      ai_msg = self.llm_with_tools.invoke(messages)
      messages.append(ai_msg)

      if not getattr(ai_msg, "tool_calls", None):
        break

      for tool_call in ai_msg.tool_calls:
        tool_name = tool_call["name"]
        args = tool_call["args"]
        if isinstance(args, str):
          args = json.loads(args)

        tool_fn = {
          "get_route_info": get_route_info
        }.get(tool_name)

        if tool_fn is None:
          raise ValueError(f"No tool found for: {tool_name}")

        tool_output = tool_fn.invoke(args)

        messages.append(
          ToolMessage(content=tool_output, tool_call_id=tool_call["id"])
        )

    raw_data = ai_msg.content
    print(raw_data)
    json_str = re.sub(r"^```json|```$", "", raw_data.strip(), flags=re.MULTILINE).strip()
    parsed_data = json.loads(json_str)
    response = Message(**parsed_data)

    shortlist_names = set(s.name for s in shortlist)
    if not response.itinerary:
      return response
    # If recommend more places
    for place in response.itinerary:
      db = get_database()
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