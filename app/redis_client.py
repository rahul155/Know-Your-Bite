import os
import redis

redis_url = os.getenv("REDIS_URL")

r = redis.from_url(redis_url, decode_responses=True)

def get_cache(key):
    return r.get(key)

def set_cache(key, value):
    r.set(key, value)