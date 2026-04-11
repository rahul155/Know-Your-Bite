import os
import json
import base64
import hashlib
from dotenv import load_dotenv
from openai import OpenAI

from app.yolo_service import detect_food_items

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 🔥 Simple in-memory cache
CACHE = {}

def get_image_hash(image_path):
    with open(image_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def analyze_image(image_path: str):
    try:
        # ================= CACHE =================
        image_hash = get_image_hash(image_path)

        if image_hash in CACHE:
            print("CACHE HIT")
            return CACHE[image_hash]

        print("CACHE MISS")

        # ================= YOLO =================
        detected_items = detect_food_items(image_path)

        # ================= BASE64 =================
        with open(image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode()

        # ================= PROMPT =================
        prompt = f"""
You are a nutrition expert.

Detected food items:
{detected_items}

IMPORTANT:
- Identify ALL food items
- Improve detected items if needed
- Estimate calories, protein, carbs, fat

Return STRICT JSON:

{{
  "food": "meal name",
  "items": [...],
  "calories": number,
  "protein": number,
  "carbs": number,
  "fat": number,
  "confidence": number_between_0_and_1
}}
"""

        # ================= OPENAI =================
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            },
                        },
                    ],
                }
            ],
            max_tokens=400,
        )

        content = response.choices[0].message.content

        # ================= PARSE =================
        result = json.loads(content)

        # ================= CACHE SAVE =================
        CACHE[image_hash] = result

        return result

    except Exception as e:
        print("AI ERROR:", e)

        # fallback response
        return {
            "food": "Unknown",
            "items": [],
            "calories": 0,
            "protein": 0,
            "carbs": 0,
            "fat": 0,
            "confidence": 0.0
        }