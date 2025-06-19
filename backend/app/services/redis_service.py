import redis
from typing import Optional, List
from app.models.session import SessionState, SlotData, ShortlistItem

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

  def load_session_state(self, user_id: str, session_id: str) -> Optional[SessionState]:
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
  def save_session_state(self, session_state: SessionState) -> bool:
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

  def update_session_title(self, user_id: str, session_id: str, new_title: str) -> Optional[SessionState]:
    session_state = self.load_session_state(user_id, session_id)
    if session_state:
      session_state.title = new_title
      self.save_session_state(session_state)
      return session_state
    return None

  def update_slots(self, user_id: str, session_id: str, new_slots: SlotData) -> Optional[SessionState]:
    session_state = self.load_session_state(user_id, session_id)
    if session_state:
      # new_slots.model_dump(exclude_unset=True) only update data provided
      session_state.slots = session_state.slots.model_copy(update=new_slots.model_dump(exclude_unset=True))
      self.save_session_state(session_state)
      return session_state
    return None

  # Deal with metadata except from title and slot
  def update_session_field(self, user_id: str, session_id: str, field_name: str, value: any) -> Optional[SessionState]:
    session_state = self.load_session_state(user_id, session_id)
    if session_state and hasattr(session_state, field_name):
      setattr(session_state, field_name, value)
      self.save_session_state(session_state)
      return session_state
    return None

  # Deal with conversation history, use redis list
  def append_history(self, user_id: str, session_id: str, message: str) -> Optional[SessionState]:
    if not self._redis_client:
      return False
    
    session_state = self.load_session_state(user_id, session_id)
    if not session_state:
      return False
    
    try:
      self._redis_client.rpush(session_state.history_key, message)
      return True
    except Exception as e:
      print(f"Error appending history for {user_id}/{session_id}: {e}")
      return False

  def get_history(self, user_id: str, session_id: str) -> List[str]:
    if not self._redis_client:
      return []
    
    session_state = self.load_session_state(user_id, session_id)
    if not session_state:
      return []
    
    # TODO: should use redis list to realize pages, not get all conversations
    return self._redis_client.lrange(session_state.history_key, 0, -1)

  # Deal with shortlist
  def add_to_shortlist(self, user_id: str, session_id: str, item: ShortlistItem) -> Optional[SessionState]:
    if not self._redis_client:
      return False
    
    session_state = self.load_session_state(user_id, session_id)
    if not session_state:
      return False
    
    try:
      item_id = item.name
      self._redis_client.hset(session_state.shortlist_key, item_id, item.model_dump_json())
      return True
    except Exception as e:
      print(f"Error adding to shortlist for {user_id}/{session_id}: {e}")

  def get_shortlist(self, user_id: str, session_id: str) -> List[ShortlistItem]:
    if not self._redis_client:
      return []
    
    session_state = self.load_session_state(user_id, session_id)
    if not session_state:
      return []
    
    try:
      items_data = self._redis_client.hgetall(session_state.shortlist_key)
      return [ShortlistItem.model_validate_json(data) for data in items_data.values()]
    except Exception as e:
      print(f"Error adding to shortlist for {user_id}/{session_id}: {e}")
      return []

  def remove_from_shortlist(self, user_id: str, session_id: str, item_id: str) -> bool:
    if not self._redis_client:
      return False
    
    session_state = self.load_session_state(user_id, session_id)
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