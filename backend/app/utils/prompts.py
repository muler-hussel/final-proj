from langchain_core.prompts import ChatPromptTemplate

# TODO maybe use xml tags
# Automatically generate trip title
GENERATE_SESSION_TITLE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an AI assistant. Based on the user's initial prompt, generate a concise and relevant title for a travel planning session.
    The title should capture the essence of the travel plan. If the prompt contains specific destination/date/preferences, incorporate them.
    If the prompt is generic, generate a general title like "New Trip".
    Keep the title short, ideally under 15 characters.
    Examples:
    - User: "I want to visit Japan" -> Title: "Trip to Japan"
    - User: "My family of three wants to go on vacation to the seaside next summer." -> Title: "Family Island Vacation"
    - User: "Help me plan a backpacking trip to Europe" -> Title: "Backpacking Trip to Europe"
    - User: "Hello" -> Title: "New Trip"
    """),
    ("human", "Initial Prompt: {prompt}\nSuggested Title:")
])

# Examples and prompt for filling slot
SLOT_FILLING_PROMPT = ChatPromptTemplate.from_messages([
  ("system", """You are an expert travel assistant. Your task is to extract specific travel-related information from the user's conversation history.
  Extract the following details:
  - destination: The user's desired travel destination (e.g., 'Paris', 'Japan', 'a beach holiday').
  - date: The user's desired travel date or period (e.g., 'next summer', 'December', 'for 5 days').
  - people: The number of people traveling (e.g., '2 adults and 1 child', 'a family of four', 'just me').
  - preferences: The user's travel preferences (e.g., 'adventure', 'relaxing', 'foodie', 'history', 'nature', 'luxury', 'budget-friendly').
  
  If a piece of information is not mentioned, leave it as null. Only extract what is explicitly stated or strongly implied.
  """),
  ("human", "{history}")
])

# Initialize todo list at the beginning of session
GENERATE_TODO_PROMPT = ChatPromptTemplate.from_messages([
  ("system", """You are a helpful AI assistant managing a user's travel planning session.
  Based on the current state of the travel planning (user_id: {user_id}, session_id: {session_id}, current_slots: {slots}), generate an initial, ordered to-do list for planning this trip.
  Each item in the list should be a clear, actionable step.
  
  **Important: The list MUST always include the following final steps:**
  - Draft a detailed itinerary.
  - Finalize itinerary document for user.
  
  Example steps (in addition to the required final steps):
  - Collect more information about user preferences.
  - Research potential destinations.
  - Research attractions in [Destination].
  - Present initial destination/attraction ideas to the user.
  - Refine suggestions based on user feedback.
  
  Return the list as a bulleted list, one item per line, starting with "- ".
  """),
  ("human", "Generate the initial to-do list.")
])

# Adjust todo list TODO
ADJUST_TODO_PROMPT = ChatPromptTemplate.from_messages([
  ("system", """You are a helpful AI assistant managing a user's travel planning session.
  The current to-do list is:
  {current_todo}
  
  The user just said: "{user_input}"
  
  Considering the user's input and the current filled slots ({slots}), adjust the to-do list if necessary.
  This might involve:
  - Marking a step as complete and moving to the next.
  - Adding new steps.
  - Reordering steps.
  - Removing irrelevant steps.
  - Staying on the current step if more information is needed.
  
  If the user explicitly asks to skip a step, mark it as done.
  Return the *updated*, ordered to-do list as a bulleted list, one item per line, starting with "- ". If no changes are needed, return the original list.
  """),
  ("human", "Update the to-do list based on my last input.")
])

# Remind of completing slots
MISSING_SLOT_PROMPT_FIRST_INPUT = """
Hello! It's a pleasure to plan the journey for you. To better assist you, I need to know some basic information: 
destination, travel date, number of travelers and your travel preferences.

Or you can:
- Click the **Next button** below and let me recommend cities and scenic spots for you first.
- Click **Your Preference** at the top right of the page at any time to fill in the form.
- Tell me directly **in the conversation** at any time!
"""

MISSING_SLOT_PROMPT_BEFORE_PLANNING = """
Great! Before generating a detailed travel route for you, please confirm or supplement the following information:

destination: {destination}
Travel date: {date}
Number of travelers: {people}
Travel preference: {preferences}

If you need to add or modify anything, please let me know.
If not, you can click the **Next button** to generate the travel route.
"""

# Response of ai TODO short & long term prompt
BASIC_PROMPT = ChatPromptTemplate.from_messages([
  ("system", """You are a polite and helpful AI travel assistant. Your goal is to guide the user through planning their trip.
  
  Current Session Context:
  User ID: {user_id}
  Session ID: {session_id}
  
  Current Filled Information:
  {slots}
  
  Current To-Do Step: {current_todo_step}
  Remaining To-Do:
  {remaining_todo}
  
  **Instructions for your response:**
  1.  **Respond to the user's input naturally.**
  2.  **Integrate Missing Information Prompt (if provided):** If `missing_info_prompt` is not empty, incorporate it naturally into your response. This prompt tells the user what information is missing.
  3.  **To-Do Step Guidance:** If `missing_info_prompt` is empty, gently guide the user to the next step in the `todo` list or explain what you are doing next. If the current step is complete, indicate progress. If the user asks to skip, acknowledge it.
  4.  **Avoid Repetitive Questions:** Do NOT repeatedly ask for missing information if `missing_info_prompt` is NOT provided by the system.
  5.  **Maintain a conversational and helpful tone.**
  """),
  ("human", "User Input: {user_input}\nMissing Information Prompt: {missing_info_prompt}")
])
