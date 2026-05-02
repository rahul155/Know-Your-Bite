from celery import Celery
import os
import base64
import json
import re
import traceback
from openai import OpenAI
from PIL import Image

celery = Celery(
    "worker",
    broker=os.getenv("REDIS_URL"),
    backend=os.getenv("REDIS_URL")
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@celery.task(bind=True)
def process_image(self, image_path):
    try:
        print("WORKER STARTED 🚀")

        # ✅ COMPRESS IMAGE (VERY IMPORTANT)
        img = Image.open(image_path)
        img = img.convert("RGB")
        img.thumbnail((800, 800))

        compressed_path = "compressed.jpg"
        img.save(compressed_path, format="JPEG", quality=70)

        # Convert to base64
        with open(compressed_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode()

        prompt = """
You are an expert nutritionist.

Analyze the image carefully.

TASK:
1. Detect if there is food
2. Identify the food accurately
3. Estimate portion size
4. Estimate nutrition

RULES:
- If ANY edible food is visible → is_food = true
- Only return false if absolutely no food
- Be specific in naming food (not "meal" unless unclear)
- Estimate portion size: small, medium, large
- Adjust calories based on portion size
- Avoid hallucinating items not visible

Return ONLY JSON:

{
  "is_food": boolean,
  "confidence": number,
  "reason": "short explanation",
  "food": "specific name",
  "items": ["item1", "item2"],
  "portion": "small | medium | large",
  "calories": number,
  "protein": number,
  "carbs": number,
  "fat": number
}
"""

        print("CALLING OPENAI...")

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

        # ✅ SAFE JSON PARSING
        try:
            result = json.loads(content)
        except:
            match = re.search(r"\{[\s\S]*\}", content)
            if match:
                result = json.loads(match.group())
            else:
                raise Exception("No JSON found in response")

        # Defaults
        result.setdefault("is_food", True)
        result.setdefault("confidence", 0.5)
        result.setdefault("reason", "")
        result.setdefault("food", "")
        result.setdefault("items", [])
        result.setdefault("calories", 0)
        result.setdefault("protein", 0)
        result.setdefault("carbs", 0)
        result.setdefault("fat", 0)

        print("FINAL RESULT:", result)

        return result

    except Exception as e:
        print("🔥 ERROR OCCURRED:")
        traceback.print_exc()

        # ✅ SAFE FALLBACK
        return {
            "is_food": True,
            "confidence": 0.3,
            "reason": "fallback due to processing error",
            "food": "Estimated meal",
            "items": ["meal"],
            "calories": 300,
            "protein": 10,
            "carbs": 40,
            "fat": 10
        }