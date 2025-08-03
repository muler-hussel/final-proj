import redis
from typing import Optional, List
from app.models.session import Message, SessionState, History, DailyItinerary
from app.models.shortlist import ShortlistItem
import asyncio
from app.db.mongodb import get_database
from app.models.db_session import DbSession
from datetime import datetime
import re
import json

class RedisService:
  _instance = None
  _redis_client: Optional[redis.Redis] = None

  def __new__(cls):
    if cls._instance is None:
      cls._instance = super(RedisService, cls).__new__(cls)
      cls._redis_client = cls._connect_redis()
    return cls._instance

  @classmethod
  # Connect to redis
  def _connect_redis(cls):
    try:
      redis_client = redis.Redis(host="127.0.0.1", port=6379, db=0, decode_responses=True)
      redis_client.ping()
      print("Connected to Redis successfully!")
      return redis_client
    except redis.exceptions.ConnectionError as e:
      print(f"Could not connect to Redis: {e}")
      return None

  def get_redis_client(self) -> Optional[redis.Redis]:
    return self._redis_client

  # Deal with session metadata
  def _get_session_metadata_key(self, user_id: str, session_id: str) -> str:
    return f"user:{user_id}:session:{session_id}:metadata"

  async def load_session_state(self, user_id: str, session_id: str) -> Optional[SessionState]:
    if not self._redis_client:
      return None

    key = self._get_session_metadata_key(user_id, session_id)
    data = self._redis_client.get(key)
    if not data:
      data = await self._get_session_from_db(user_id, session_id)
    if data:
      try:
        return SessionState.model_validate_json(data)
      except Exception as e:
        print(f"Error loading session state for {user_id}: {e}")
        return None
    return data

  async def load_session_with_userId(self, user_id: str):
    pattern = f"user:{user_id}:session:*:metadata"
    cursor = b"0"
    sessions = []

    while cursor:
      cursor, keys = self._redis_client.scan(cursor=cursor, match=pattern, count=100)
      for key in keys:
        match = re.search(rf"user:{user_id}:session:(.*):metadata", key)
        if match:
          session_id = match.group(1)
          raw_data = self._redis_client.get(key)
          if not raw_data:
            continue
          try:
            data = json.loads(raw_data)
            title = data.get("title", "")
            update_time_str = data.get("update_time")
            update_time = datetime.fromisoformat(update_time_str) if update_time_str else datetime.min
            sessions.append({
              "session_id": session_id,
              "title": title,
              "update_time": update_time
            })
          except Exception as e:
            print(f"Error parsing session metadata for {session_id}: {e}")
      if cursor == b"0":
        break

    sessions.sort(key=lambda x: x["update_time"], reverse=True)
    return sessions
  
  async def save_from_db(self, session_state: SessionState) -> bool:
    if not self._redis_client:
      return False

    key = session_state.get_redis_key()
    try:
      json_data = session_state.model_dump_json()
      # history = session_state.history
      # shortlist = session_state.shortlist
      # for h in history:
      #   self._redis_client.rpush(session_state.history_key, h.model_dump_json())
      # for s in shortlist:
      #   self._redis_client.hset(session_state.shortlist_key, s.name, s.model_dump_json())

      self._redis_client.set(key, json_data, ex=3600)
      return True
    except Exception as e:
      print(f"Error saving session state for {session_state.user_id}/{session_state.session_id}: {e}")
      return False

  async def save_session_state(self, session_state: SessionState) -> bool:
    if not self._redis_client:
      return False

    key = session_state.get_redis_key()
    try:
      session_state.update_time = datetime.now()
      json_data = session_state.model_dump_json()
      self._redis_client.set(key, json_data, ex=3600)

      asyncio.create_task(self._session_to_mongodb(session_state))
      return True
    except Exception as e:
      print(f"Error saving session state for {session_state.user_id}/{session_state.session_id}: {e}")
      return False

  async def update_session_title(self, user_id: str, session_id: str, new_title: str) -> Optional[SessionState]:
    session_state = await self.load_session_state(user_id, session_id)
    if session_state:
      session_state.title = new_title
      await self.save_session_state(session_state)
      return session_state
    return None

  async def delete_session(self, user_id: str, session_id: str) -> bool:
    histroy_key = "user:{user_id}:session:{session_id}:history"
    shortlist_key = "user:{user_id}:session:{session_id}:shortlist"
    meta_key = self._get_session_metadata_key(user_id, session_id)

    try:
      self.delete(histroy_key)
      self.delete(shortlist_key)
      self.delete(meta_key)

      asyncio.create_task(self._delete_session_in_db(user_id, session_id))
      return True
    except Exception as e:
      print(f"Fail to delete session {user_id}/{session_id}: {e}")
      return False

  # Deal with metadata except from title and slot
  async def update_session_field(self, user_id: str, session_id: str, field_name: str, value: any) -> Optional[SessionState]:
    session_state = await self.load_session_state(user_id, session_id)
    if session_state and hasattr(session_state, field_name):
      setattr(session_state, field_name, value)
      await self.save_session_state(session_state)
      return session_state
    return None

  # Deal with conversation history, use redis list
  async def append_history(self, session_state: SessionState, history: History) -> bool:
    if not self._redis_client:
      return False
    
    if not session_state:
      return False
    
    try:
      self._redis_client.rpush(session_state.history_key, history.model_dump_json())
      asyncio.create_task(self._history_to_mongodb(session_state))
      return True
    except Exception as e:
      print(f"Error appending history for {session_state.user_id}/{session_state.session_id}: {e}")
      return False

  async def get_history(self, user_id: str, session_id: str) -> List[History]:
    if not self._redis_client:
      return []
    
    session_state = await self.load_session_state(user_id, session_id)

    if not session_state:
      return []
    
    history = self._redis_client.lrange(session_state.history_key, 0, -1)
    return [History(**json.loads(msg)) for msg in history]
  
  async def get_simplified_history(self, session_state: SessionState) -> str:
    history = await self.get_history(session_state.user_id, session_state.session_id)
    history_str = '\n'.join(
      f"{h.role}: {self._format_message_content(h.message)}"
      for h in history
    )
    return history_str

  # Handle with itinerary
  async def save_itinerary(self, session_state: SessionState, itinerary: DailyItinerary, chat_idx: int):
    history = await self.get_history(session_state.user_id, session_state.session_id)
    if (chat_idx >= len(history)) or (history[chat_idx].role != 'ai') :
      print("Trying to modify a wrong message")
      return False
    
    cur_history = history[chat_idx]
    cur_history.message.itinerary = itinerary
    self._redis_client.lset(session_state.history_key, chat_idx, cur_history.model_dump_json())
    asyncio.create_task(self._history_to_mongodb(session_state))
    return True

  # Deal with place infomation
  async def get_place_info(self, place_name: str) -> ShortlistItem:
    if not self._redis_client:
      return None
    
    data = self._redis_client.get(place_name)
    if data:
      try:
        return ShortlistItem.model_validate_json(data)
      except Exception as e:
        print(f"Error loading place infomation of {place_name}: {e}")
        return None
    return None
  
  async def save_place_info(self, place_name: str, place_info: ShortlistItem) -> bool:
    if not self._redis_client:
      return False
    
    try:
      json_data = place_info.model_dump_json()
      self._redis_client.set(place_name, json_data, ex=3600)
      return True
    except Exception as e:
      print(f"Error saving place information for {place_name}: {e}")
      return False
  
  # Deal with shortlist
  async def add_to_shortlist(self, session_state: SessionState, item: ShortlistItem) -> bool:
    if not self._redis_client:
      return False
    
    try:
      item_id = item.name
      self._redis_client.hset(session_state.shortlist_key, item_id, item.model_dump_json())
      asyncio.create_task(self._shortlist_to_mongodb(session_state))
      return True
    except Exception as e:
      print(f"Error adding to shortlist for {session_state.user_id}/{session_state.session_id}: {e}")
      return False

  async def get_shortlist(self, user_id: str, session_id: str) -> List[ShortlistItem]:
    if not self._redis_client:
      return []
    
    session_state = await self.load_session_state(user_id, session_id)

    if not session_state:
      return []
    
    try:
      items_data = self._redis_client.hgetall(session_state.shortlist_key)
      return [ShortlistItem.model_validate_json(data) for data in items_data.values()]
    except Exception as e:
      print(f"Error adding to shortlist for {session_state.user_id}/{session_state.session_id}: {e}")
      return []

  async def remove_from_shortlist(self, session_state: SessionState, item_id: str) -> bool:
    if not self._redis_client:
      return False
    
    try:
      self._redis_client.hdel(session_state.shortlist_key, item_id)
      asyncio.create_task(self._shortlist_to_mongodb(session_state))
      return True
    except Exception as e:
      print(f"Error removing from shortlist for {session_state.user_id}/{session_state.session_id}: {e}")
      return False
  
  # Redis key for asynio functions
  def get(self, key: str) -> Optional[str]:
    return self._redis_client.get(key)

  def set(self, key: str, value: str, ex: int = 300):
    self._redis_client.set(key, value, ex=ex)

  def delete(self, key: str):
    self._redis_client.delete(key)

  # helper functions
  async def _session_to_mongodb(self, session_state: SessionState):
    db = get_database()
    try:
      await DbSession(db).save_session(session_state)
    except Exception as e:
      print(f"ERROR: Background save to MongoDB failed for {session_state.user_id}/{session_state.session_id}: {e}")
  
  async def _history_to_mongodb(self, session_state: SessionState):
    db = get_database()
    user_id = session_state.user_id
    session_id = session_state.session_id
    history = await self.get_history(user_id, session_id)
    
    try:
      await DbSession(db).save_history(user_id, session_id, history)
    except Exception as e:
      print(f"ERROR: Background save to MongoDB failed for {session_state.user_id}/{session_state.session_id}: {e}")

  async def _shortlist_to_mongodb(self, session_state: SessionState):
    db = get_database()
    user_id = session_state.user_id
    session_id = session_state.session_id
    shortlist = await self.get_shortlist(user_id, session_id)

    try:
      await DbSession(db).save_shortlist(user_id, session_id, shortlist)
    except Exception as e:
      print(f"ERROR: Background save to MongoDB failed for {session_state.user_id}/{session_state.session_id}: {e}")

  async def _get_session_from_db(self, user_id: str, session_id: str):
    db = get_database()
    data = await DbSession(db).get_sesssion(user_id, session_id)
    if data:
      await self.save_from_db(data)
    return data
  
  async def _delete_session_in_db(self, user_id: str, session_id: str):
    db = get_database()
    await DbSession(db).delete_session(user_id, session_id)
  
  def _format_message_content(self, message: Message) -> str:
    parts = []
    parts = [
      message.content,
      str(message.itinerary) if message.itinerary else None,
      ','.join(r.name for r in message.recommendations) if getattr(message, 'recommendations', None) else None,
      ','.join(p.name for p in message.populars) if getattr(message, 'populars', None) else None
    ]
    return ' '.join(filter(None, parts))

# Ensure single instance
redis_service = RedisService()