from celery import Celery
import os
import base64
import json
import re
from openai import OpenAI

celery = Celery(
    "worker",
    broker=os.getenv("REDIS_URL"),
    backend=os.getenv("REDIS_URL")
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@celery.task(bind=True)
def process_image(self, image_path):
    try:
        print("NEW WORKER RUNNING 🚀")

        # Read image → base64
        with open(image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode()

        prompt = """
You are an expert nutritionist.

Task:
1) Determine if the image contains ANY edible food.
2) If yes, estimate nutrition.

Rules:
- If ANY edible item is visible (even multiple small dishes, mixed meals, unclear items), set "is_food": true.
- Only set "is_food": false if you are highly certain there is no food at all.
- Do not be overly strict.

Return JSON ONLY in this exact format:

{
  "is_food": boolean,
  "confidence": number,
  "reason": "short explanation",
  "food": "meal name or general label",
  "items": ["item1", "item2"],
  "calories": number,
  "protein": number,
  "carbs": number,
  "fat": number
}
"""

        print("CALLING OPENAI")

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
            max_tokens=500,
        )

        content = response.choices[0].message.content
        print("RAW RESPONSE:", content)

        # Extract JSON safely
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if not match:
            raise Exception("Invalid JSON from model")

        result = json.loads(match.group())

        # Ensure keys exist (safe defaults)
        result.setdefault("is_food", True)
        result.setdefault("confidence", 0.5)
        result.setdefault("reason", "")
        result.setdefault("food", "")
        result.setdefault("items", [])
        result.setdefault("calories", 0)
        result.setdefault("protein", 0)
        result.setdefault("carbs", 0)
        result.setdefault("fat", 0)

        # ✅ Soft override (model-aware, NOT hardcoded)
        if result.get("is_food") is False:
            confidence = result.get("confidence", 0)
            reason = str(result.get("reason", "")).lower()

            # If model is unsure or mentions food-like context → treat as food
            if confidence < 0.6 or any(x in reason for x in ["food", "meal", "dish", "plate", "edible"]):
                print("SOFT OVERRIDE: uncertain → treating as food")
                result["is_food"] = True

        print("FINAL RESULT:", result)
        return result

    except Exception as e:
        print("ERROR:", str(e))
        return {
            "is_food": False,
            "confidence": 0,
            "reason": "error processing image",
            "food": "",
            "items": [],
            "calories": 0,
            "protein": 0,
            "carbs": 0,
            "fat": 0
        }