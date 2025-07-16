from redis.asyncio import Redis

class RedisExpiredListener:
  def __init__(self, redis_url: str):
    self.redis_url = redis_url
      
  async def listen(self):
    redis = Redis(host="localhost", port=6379, db=0)
    pubsub = redis.pubsub()
    await pubsub.subscribe("__keyevent@0__:expired")
    print("RedisExpiredListener: Subscribed to expired key events.")

    async for message in pubsub.listen():
      if message["type"] == "message":
        expired_key = message["data"].decode()

        # key: user:{user_id}:session:{session_id}:metadata
        parts = expired_key.split(":")
        if len(parts) == 5 and parts[4] == "metadata":
          user_id = parts[1]
          session_id = parts[3]

          base_key = f"user:{user_id}:session:{session_id}"
          history_key = f"{base_key}:history"
          shortlist_key = f"{base_key}:shortlist"
          
          try:
            # Explicitly delete the related keys in Redis
            # Use pipeline for atomic deletion.
            pipe = redis.pipeline()
            pipe.delete(history_key)
            pipe.delete(shortlist_key)
            await pipe.execute()
          except Exception as ex:
            print(f"RedisExpiredListener: ERROR during cleanup for {user_id}/{session_id}: {ex}")