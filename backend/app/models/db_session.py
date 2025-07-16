from pymongo import IndexModel, ASCENDING
from app.models.session import SessionState, History
from typing import List
from app.models.shortlist import ShortlistItem

class DbSession:
  def __init__(self, db):
    self.collection = db["session"]

  async def _create_indexes(self):
    await self.collection.create_indexes([
      IndexModel([("user_id", ASCENDING), ("session_id", ASCENDING)], unique = True)
    ])

  async def get_sesssion(self, user_id: str, session_id: str) -> SessionState | None:
    data = await self.collection.find_one({"user_id": user_id, "session_id": session_id})
    if data:
      data.pop("_id", None)
      return SessionState(**data)
    return None

  async def get_sessions_by_user_id(self, user_id: str) -> List[SessionState]:
    cursor = self.collection.find({"user_id": user_id})
    docs = await cursor.to_list(length=None)
    session_states = [SessionState(**doc) for doc in docs]
    return session_states

  async def save_session(self, session: SessionState):
    result = await self.collection.update_one(
      {"user_id": session.user_id, "session_id": session.session_id},
      {"$set": session.model_dump(exclude={"history", "shortlist"})},
      upsert=True
    )

    if result.matched_count > 0:
      print(f"MongoDB: Updated session for user {session.user_id}, session {session.session_id}. Modified count: {result.modified_count}")
    else:
      print(f"MongoDB: No session found for user {session.user_id}, session {session.session_id} to update history.")

  async def save_history(self, user_id: str, session_id: str, history: List[History]):
    # Serialize to List[dict]
    history_dicts = [item.model_dump() for item in history]
    result = await self.collection.update_one(
      {"user_id": user_id, "session_id": session_id},
      {"$set": {"history": history_dicts}}, 
      upsert=True
    )
    
    if result.matched_count > 0:
      print(f"MongoDB: Updated history for user {user_id}, session {session_id}. Modified count: {result.modified_count}")
    else:
      print(f"MongoDB: No session found for user {user_id}, session {session_id} to update history.")

  async def save_shortlist(self, user_id: str, session_id: str, shortlist: List[ShortlistItem]):
    # Serialize to List[dict]
    shortlist_dicts = [item.model_dump() for item in shortlist]
    result = await self.collection.update_one(
      {"user_id": user_id, "session_id": session_id},
      {"$set": {"shortlist": shortlist_dicts}}, 
      upsert=False
    )
    
    if result.matched_count > 0:
      print(f"MongoDB: Updated history for user {user_id}, session {session_id}. Modified count: {result.modified_count}")
    else:
      print(f"MongoDB: No session found for user {user_id}, session {session_id} to update history.")
