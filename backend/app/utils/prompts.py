from langchain_core.prompts import ChatPromptTemplate

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

# Identify relations between user prompts and todo list
INTENT_CLASSIFIER_PROMPT = ChatPromptTemplate([
  ("system", """You are an intent classification AI. Your task is to analyze the user's input and classify their primary intent based on the predefined categories.
  Focus solely on identifying the intent; do not generate a conversational response.

  **Predefined Intent Categories:**
  - ADVANCE_STEP: User wants to move to the next logical step in the planning process, or confirms current step is complete.
  - MORE_RECOMMENDATIONS: User asks for more options or specific ideas (e.g., "show more", "focus on").
  - ITINERARY_GENERATION: User explicitly asks to generate an itinerary.
  - GENERAL_QUERY: User asks a question that is not directly about advancing the planning flow or changing core plan details, but seeks general information (e.g., "What are the visa requirements for France?").
  - MODIFY_PLAN: User has explicitly changed a fundamental planning detail (e.g., destination, dates, main travel type/season, preferences). This implies a potential reset or significant re-evaluation of the current plan.
  - FINALIZE_TRIP: User explicitly asks to generate a final itinerary with more information (e.g., hotel, transport, restaurant).
  - OTHER: For any other intent not fitting above.
   
  Output your one or several intent types as a JSON array of strings.
  """),
  ("human", "User input: {user_input}\n")
])

# Remind of completing slots
PROMPT_FIRST_INPUT = """
Hello! It's a pleasure to plan the journey for you. To better assist you, I hope you can provide more and specific travel preferences.

You can:
- Click **Your Preference** at the top right of the page at any time to see your prefrences summarized by me, feel free to add, delete or modify them.
- Tell me directly in the conversation **at any time**!
"""

# Response of ai TODO: short & long term prompt
BASIC_PROMPT = ChatPromptTemplate([
  ("system", """You are a polite and helpful AI travel assistant. Your goal is to guide the user through planning their trip.
  
  Current Session Context:
  User ID: {user_id}
  Session ID: {session_id}
  History: {history}
  
  **Instructions for your response:**
  1.  **Respond to the user's input naturally.**
  2.  **If `first_prompt` is not empty**, you must:
      - Fully and naturally include all content from `first_prompt` in your reply.
      - Do not shorten or omit any information from it.
      - You may paraphrase slightly to match the conversation tone, but **all bullet points and core ideas must appear** in your reply.
  3.  **To-Do Step Guidance:** Gently guide the user to the next step in the `todo_prompt` or explain what you are doing next. If the current step is complete, indicate progress. If the user asks to skip, acknowledge it.
  4.  **Avoid Repetitive Questions:** Do NOT repeatedly ask for more information if `first_prompt` is NOT provided by the system.
  5.  **Maintain a conversational and helpful tone.**
  """),
  ("human", "User Input: {user_input}\nFirst Prompt: {first_prompt}\ntodo: {todo_prompt}")
])

# Extract preferences from user behavior or input
EXTRACT_PREFERENCES_PROMPT = ChatPromptTemplate([
    ("system", """You are a travel preference analysis assistant.
    Your task is to infer travel preference styles based on user interactions and explicit statements.

    **Guidance for Inference:**
    1.  **From `places`:** If the `places` list is not empty, each place name signifies a positive interaction and indicates a potential area of interest. For each place in the `places` list, infer **one to two distinct travel preference styles** that are strongly suggested by that specific location.
    2.  **From `user_input`:** Analyze the `user_input` to identify any **explicitly stated dislikes or strong avoidance styles**. These should be clear and unequivocal.

    **Output Format:**
    Always return a JSON object with the following two keys:
    1.  `preferences`: A list of objects. Each object must have two keys:
        * `place`: The name of the place from which the preference was inferred (e.g., "Paris").
        * `preference`: A list of 1 or 2 inferred preference styles for that specific place (e.g., ["Romantic Getaway", "Cultural Exploration"]).
    2.  `avoid`: A list of clearly identified avoidance styles or characteristics based on the user's explicit dislikes (e.g., ["Crowded Tourist Traps", "Extreme Sports"]).

    **Examples of Preference Styles (for guidance, not exhaustive):**
    * Adventure Travel
    * Beach Relaxation
    * Cultural Immersion

    **Examples of Avoidance Styles (for guidance, not exhaustive):**
    * Overly Commercialized
    * Loud Environments

    """),
    ("human", "Place list: {places}\nUser input: {user_input}\n\n")
])

RECOMMEND_NEW_PLACES_PROMPT = ChatPromptTemplate([
  ("system", """You are a highly skilled travel recommendation AI. Your goal is to suggest **no more than six new travel destinations** that align with the user's preferences while strictly avoiding any places already listed in `recommended_places`.

  **Consider the following information for your recommendations, prioritizing available data:**

  1.  **User Input (`user_input`):** This is always present and the most immediate indicator of current interests or specific requests. Prioritize explicit mentions here.
  2.  **Short-Term Profile (`short_term_profile`):** (May be empty)
      * If available, `preferences` indicate recent interests from the current session. Higher `weight` values indicate stronger recent interest.
      * If available, `avoids` indicate immediate dislikes from the current session. Strictly avoid any destinations or characteristics matching these.
  3.  **Long-Term Profile (`long_term_profile`):** (May be empty)
      * If available, `verified_preferences` are established, strong, and consistent preferences. Higher `weight` values indicate stronger recent interest.
      * If available, `decaying_preferences` are past preferences that might still hold some interest but are less strong than `verified_preferences`.
      * If available, `avoids` are long-standing dislikes. Strictly avoid any destinations or characteristics matching these.

  **Output Format:**
  Return a JSON object with two keys:
    1.  `content`: A string containing an introductory remark, a summary of findings, or direct answers to any additional questions posed in `user_input` (e.g., "To visit France, you'll generally need a Schengen visa if you're not from a visa-exempt country. Here are some places you might enjoy:"). This should be natural conversational text.
    2.  `recommendations`: A JSON array including a list of objects, each with two keys:
        * `place_name`: The name of the recommended place.
        * `description`: Recommending reason for this place, no more than 20 words.
        * `recommend_reason`: Longer recommending reason for this place, no more than 100 words.

    If no suitable recommendations can be found, the `recommendations` array should be empty.
  ```

  """),
  ("human", "User input: {user_input}\nLong-term profile: {long_term_profile}\nShort-term profile: {short_term_profile}\nAlready recommended places: {recommended_places}\n\n")
])