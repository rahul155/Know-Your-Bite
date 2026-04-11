def get_calories(food_name):
    # Simple mock (fast MVP)
    dummy_db = {
        "rice": 200,
        "biryani": 600,
        "pizza": 300,
        "burger": 350,
        "idli": 150,
        "dosa": 250
    }

    calories = dummy_db.get(food_name.lower(), 250)

    return {
        "calories": calories,
        "protein": 10,
        "carbs": 30,
        "fat": 8
    }