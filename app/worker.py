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

        # Read image and convert to base64
        with open(image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode()

        prompt = """
You are an expert nutritionist.

Analyze the image carefully.

CRITICAL RULES:

- If the image clearly contains NO edible items (e.g., bottle, phone, furniture), return:
{
  "is_food": false,
  "confidence": 0
}

- If the image contains ANY edible items (even if multiple items, mixed meals, or unclear), treat it as FOOD and return:
{
  "is_food": true,
  "food": "general meal name (e.g., mixed meal, snack, dish name if clear)",
  "items": ["list of visible food items"],
  "calories": realistic estimate,
  "protein": number,
  "carbs": number,
  "fat": number,
  "confidence": number
}

IMPORTANT:
- Meals may contain multiple items → still treat as food
- Even partial or unclear food → treat as food
- Only return false if absolutely certain there is no food
- Do not hallucinate non-existent items, but provide best estimate if visible

Only return valid JSON.
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
            max_tokens=400,
        )

        content = response.choices[0].message.content
        print("RAW RESPONSE:", content)

        # Extract JSON safely
        match = re.search(r"\{.*\}", content, re.DOTALL)

        if not match:
            raise Exception("Invalid JSON from model")

        result = json.loads(match.group())

        # Ensure is_food exists
        if "is_food" not in result:
            result["is_food"] = True

        # Prevent false negatives
        if result.get("is_food") is False:
            if any(k in result for k in ["food", "items", "calories"]):
                result["is_food"] = True

        print("FINAL RESULT:", result)

        return result

    except Exception as e:
        print("ERROR:", str(e))

        # Safe fallback
        return {
            "is_food": False,
            "confidence": 0
        }