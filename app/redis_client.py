import redis
import json

# ✅ create client directly
redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)

def get_cache(key):
    data = redis_client.get(key)
    return json.loads(data) if data else None

def set_cache(key, value):
    redis_client.set(key, json.dumps(value), ex=3600)