import hashlib
import json
import os

CACHE_FILE = "cache.json"

# Load cache
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r") as f:
        CACHE = json.load(f)
else:
    CACHE = {}

def get_image_hash(file_path):
    with open(file_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def get_cached_result(image_hash):
    return CACHE.get(image_hash)

def save_cache(image_hash, result):
    CACHE[image_hash] = result
    with open(CACHE_FILE, "w") as f:
        json.dump(CACHE, f)