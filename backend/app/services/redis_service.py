import redis
from typing import Optional, List
from app.models.session import SessionState
from app.models.shortlist import ShortlistItem
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
    if data:
      try:
        return SessionState.model_validate_json(data)
      except Exception as e:
        print(f"Error loading session state for {user_id}: {e}")
        return None
    return None

  # TODO: set expire time; store data in mongodb; delete history and shortlist according to keys
  async def save_session_state(self, session_state: SessionState) -> bool:
    if not self._redis_client:
      return False

    key = session_state.get_redis_key()
    try:
      json_data = session_state.model_dump_json()
      self._redis_client.set(key, json_data)
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

  # Deal with metadata except from title and slot
  async def update_session_field(self, user_id: str, session_id: str, field_name: str, value: any) -> Optional[SessionState]:
    session_state = await self.load_session_state(user_id, session_id)
    if session_state and hasattr(session_state, field_name):
      setattr(session_state, field_name, value)
      await self.save_session_state(session_state)
      return session_state
    return None

  # Deal with conversation history, use redis list
  async def append_history(self, session_state: SessionState, message: str, role: str) -> Optional[SessionState]:
    if not self._redis_client:
      return False
    
    if not session_state:
      return False
    
    history = {
      "role": role,
      "message": message
    }
    try:
      self._redis_client.rpush(session_state.history_key, json.dumps(history))
      return True
    except Exception as e:
      print(f"Error appending history for {session_state.user_id}/{session_state.session_id}: {e}")
      return False

  async def get_history(self, user_id: str, session_id: str) -> List[str]:
    if not self._redis_client:
      return []
    
    session_state = await self.load_session_state(user_id, session_id)
    if not session_state:
      return []
    
    history = self._redis_client.lrange(session_state.history_key, 0, -1)
    return [json.loads(msg) for msg in history]

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
      self._redis_client.set(place_name, json_data)
      return True
    except Exception as e:
      print(f"Error saving place information for {place_name}: {e}")
      return False
  
  # Deal with shortlist
  async def add_to_shortlist(self, user_id: str, session_id: str, item: ShortlistItem) -> Optional[SessionState]:
    if not self._redis_client:
      return False
    
    session_state = await self.load_session_state(user_id, session_id)
    if not session_state:
      return False
    
    try:
      item_id = item.name
      self._redis_client.hset(session_state.shortlist_key, item_id, item.model_dump_json())
      return True
    except Exception as e:
      print(f"Error adding to shortlist for {user_id}/{session_id}: {e}")

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
      print(f"Error adding to shortlist for {user_id}/{session_id}: {e}")
      return []

  async def remove_from_shortlist(self, user_id: str, session_id: str, item_id: str) -> bool:
    if not self._redis_client:
      return False
    
    session_state = await self.load_session_state(user_id, session_id)
    if not session_state:
      return False
    
    try:
      self._redis_client.hdel(session_state.shortlist_key, item_id)
      return True
    except Exception as e:
      print(f"Error removing from shortlist for {user_id}/{session_id}: {e}")
      return False
  
# Ensure single instance
redis_service = RedisService()