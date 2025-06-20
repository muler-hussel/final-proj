from langchain_core.prompts import ChatPromptTemplate

# TODO: maybe use xml tags
# Automatically generate trip title
GENERATE_SESSION_TITLE_PROMPT = ChatPromptTemplate([
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
# In case user change or delete something, like changing from 'summer' to 'winter'
SLOT_FILLING_PROMPT = ChatPromptTemplate([
  ("system", """You are an expert travel assistant. Your task is to extract specific travel-related information from the user's conversation history.
  Extract the following details:
  - destination: The user's desired travel destination (e.g., 'Paris', 'Japan', 'a beach holiday').
  - date: The user's desired travel date or period (e.g., 'next summer', 'December', 'for 5 days').
  - people: The number of people traveling (e.g., '2 adults and 1 child', 'a family of four', 'just me').
  - preferences: The user's travel preferences (e.g., 'adventure', 'relaxing', 'foodie', 'history', 'nature', 'luxury', 'budget-friendly').
  
  If a piece of information is not mentioned, leave it as null. Only extract what is explicitly stated or strongly implied.
  
  **Crucially, if new information directly contradicts or replaces a previously known value({slots}) for a slot (e.g., a new destination, new dates, new season), you MUST provide the new value.  For preferences, generally append new ones unless they directly contradict previous ones.**
  """),
  ("human", "User: {history}")
])

# Initialize todo list at the beginning of session
# First step is always manually set as MISSING_SLOT_PROMPT_FIRST_INPUT if missing slots exist
GENERATE_TODO_PROMPT = ChatPromptTemplate([
  ("system", """You are a helpful AI assistant managing a user's travel planning session.
  Based on the current travel planning state(user_id:{user_id}, session_id:{session_id}, user_input:{user_input}), generate an initial, ordered to-do list.
  Each item must have a 'description' (the actionable step) and a 'type' (a predefined category).

  **Allowed 'type' categories:**
  - RESEARCH_DESTINATIONS: For broad research on potential travel locations.
  - RESEARCH_ATTRACTIONS: For researching specific points of interest within a chosen destination.
  - RESEARCH_SPECIFIC_ITEM: For researching a specific type of item (e.g., "restaurants", "hotels", "transport").
  - PRESENT_IDEAS: For compiling and presenting options to the user.
  - REFINE_SUGGESTIONS: For adjusting options based on user feedback or "load more" requests.
  - DRAFT_ITINERARY: For creating the detailed day-by-day plan.
  - FINALIZE_DOCUMENT: For preparing the final, ready-to-present document.
  - OTHER: For any other general planning step not fitting above.

  **Important: The list MUST always include the final steps:**
  - type: DRAFT_ITINERARY, description: "Draft a detailed itinerary."
  - type: FINALIZE_DOCUMENT, description: "Finalize itinerary document for user."
    
  **Important: The list SHOULD NOT contain steps for gathering user preferences**

  **Example Output Format:**
  ```json
  [
    {"description": "Research vegetarian-friendly restaurants in Austin.", "type": "RESEARCH_SPECIFIC_ITEM"},
    {"description": "Evaluate restaurants based on ambiance and user reviews.", "type": "OTHER"}, # Or a more specific 'EVALUATE_OPTIONS' type
    {"description": "Compile a list of top vegetarian-friendly restaurants with great ambiance in Austin.", "type": "PRESENT_IDEAS"},
    {"description": "Refine restaurant suggestions based on user feedback.", "type": "REFINE_SUGGESTIONS"},
    {"description": "Research other attractions and activities in Austin to complement dining experiences.", "type": "RESEARCH_SPECIFIC_ITEM"},
    {"description": "Present additional activity options to the user.", "type": "PRESENT_IDEAS"},
    {"description": "Refine activity suggestions based on user feedback.", "type": "REFINE_SUGGESTIONS"},
    {"description": "Draft a detailed itinerary.", "type": "DRAFT_ITINERARY"},
    {"description": "Finalize itinerary document for user.", "type": "FINALIZE_DOCUMENT"}
  ]
  ```

  Return the list as a JSON array as shown above.
  """),
  ("human", "Generate the initial to-do list.")
])

# Adjust todo list
ADJUST_TODO_PROMPT = ChatPromptTemplate.from_messages([
  ("system", """You are a highly intelligent AI planning assistant. Your core task is to dynamically manage a user's travel planning to-do list.
  Based on the current session state, any new user input, or explicit user actions, you must determine the optimal to-do list and the exact step the planning process should be on.

  **Current Session State:**
  User ID: {user_id}
  Session ID: {session_id}
  Current Slots: {slots}
  Current To-Do List: {current_todo_list} (list of strings, indexed from 0)
  Current Step Index: {current_step_index} (index of the step currently being worked on)
  Conversation History: {user_input}
  Classified Intent: {intent}

  **Rules for To-Do List Adjustment & Step Determination:**
  1.  **Always include:** "- Draft a detailed itinerary." and "- Finalize itinerary document for user." as the final steps.
  2.  **Research & Presentation:**
      * "Research potential destinations." and "Research attractions in [Destination]." are AI-driven, AI should automatically advance through these.
      * "Present initial destination/attraction ideas to the user." is where AI makes an output.
  3.  **Refinement Loop:**
      * If the `user_input` is "LOAD_MORE_SUGGESTIONS_CLICKED", the process should STAY on "Refine suggestions based on user feedback." to provide more options.
  4.  **Generate Itinerary:**
      * If the `user_input` is "GENERATE_ITINERARY_CLICKED", the process should immediately jump to "Draft a detailed itinerary.".
  5.  **Mid-flow Changes/Interruptions:**
      * If `user_input` indicates a *significant change* in planning (e.g., "Actually, I want to go to Italy instead of Japan", "Instead of December, I want to go in summer"), the entire `todo_list` might need to be regenerated from scratch, and the `current_step_index` reset appropriately (e.g., back to research for the new destination).
      * If `user_input` asks a specific question (e.g., "What are the visa requirements for France?"), the `todo_list` might not change, but the `current_step_index` might need to be temporarily paused or maintained while the AI answers the question out-of-band.

  Your output MUST be a JSON object with two keys:
  `new_todo_list`: An array of strings representing the re-evaluated ordered to-do list.
  `new_current_step_index`: An integer representing the 0-based index of the step that should be executed NEXT.

  Example JSON output:
  ```json
  {
    "new_todo_list": [
      "- Collect more information about user preferences.",
      "- Research potential destinations.",
      "- Present initial destination/attraction ideas to the user.",
      "- Refine suggestions based on user feedback.",
      "- Draft a detailed itinerary.",
      "- Finalize itinerary document for user."
    ],
    "new_current_step_index": 0
  }
  ```
  """),
  ("human", "Evaluate the planning process based on new information.")
])

# Identify relations between user prompts and todo list
INTENT_CLASSIFIER_PROMPT = ChatPromptTemplate([
  ("system", """You are an intent classification AI. Your task is to analyze the user's input and classify their primary intent based on the predefined categories.
  Focus solely on identifying the intent; do not generate a conversational response.

  **Predefined Intent Categories:**
  - ADVANCE_STEP: User wants to move to the next logical step in the planning process, or confirms current step is complete.
  - MORE_RECOMMENDATIONS: User explicitly asks for more options or ideas (e.g., "show more", "load more").
  - ITINERARY_GENERATION: User explicitly asks to generate the final itinerary.
  - GENERAL_QUERY: User asks a question that is not directly about advancing the planning flow or changing core plan details, but seeks general information.
  - RESET_PLAN: User explicitly asks to start the entire planning process from scratch.
  - OTHER: For any other intent not fitting above.
   
  Output your one or several intent types as a JSON object.
  """),
  ("human", "User input: {user_input}\n\nExisting Slots: {existing_slots_json}")
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

# Response of ai TODO: short & long term prompt
BASIC_PROMPT = ChatPromptTemplate([
  ("system", """You are a polite and helpful AI travel assistant. Your goal is to guide the user through planning their trip.
  
  Current Session Context:
  User ID: {user_id}
  Session ID: {session_id}
  
  Current To-Do Step: {current_todo_step}
  History: {history}
  
  **Instructions for your response:**
  1.  **Respond to the user's input naturally.**
  2.  **Integrate Missing Information Prompt (if provided):** If `missing_info_prompt` is not empty, incorporate it naturally into your response. This prompt tells the user what information is missing.
  3.  **To-Do Step Guidance:** If `missing_info_prompt` is empty, gently guide the user to the next step in the `todo` list or explain what you are doing next. If the current step is complete, indicate progress. If the user asks to skip, acknowledge it.
  4.  **Avoid Repetitive Questions:** Do NOT repeatedly ask for missing information if `missing_info_prompt` is NOT provided by the system.
  5.  **Maintain a conversational and helpful tone.**
  """),
  ("human", "User Input: {user_input}\nMissing Information Prompt: {missing_info_prompt}")
])
