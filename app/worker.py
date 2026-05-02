from celery import Celery
import os
import base64
import json
import re
from openai import OpenAI

celery = Celery("worker", broker=os.getenv("REDIS_URL"), backend=os.getenv("REDIS_URL"))

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@celery.task(bind=True)
def process_image(self, image_path):
    try:
        print("START PROCESSING")
        with open(image_path, "rb") as f:
            mage_base64 = base64.b64encode(f.read()).decode()

            prompt = """
    You are an expert nutritionist.

Analyze the image carefully.

CRITICAL RULES:

If NOT food → return:
{"is_food": false, "confidence": 0}
If food → return:
{
"is_food": true,
"food": "meal name",
"items": ["food1"],
"calories": number,
"protein": number,
"carbs": number,
"fat": number,
"confidence": number
}

Only return JSON.
"""
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

            match = re.search(r"\{.*\}", content, re.DOTALL)

            if not match:
                raise Exception("Invalid JSON")

            result = json.loads(match.group())

            if "is_food" not in result:
                result["is_food"] = True

            return result

    except Exception as e:
        print("ERROR:", str(e))
        return {"is_food": False, "confidence": 0}
