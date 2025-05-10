from openai import OpenAI
client = OpenAI()


# noinspection PyTypeChecker
def parse_workout(text):
    prompt = f"""
You are a fitness assistant. A user will describe their workout in natural language.
Convert it into a strict JSON object with only the fields needed.

Format:
{{
  "entries": [
    {{
      "type": "strength",
      "exercise": "squats",
      "sets": 3,
      "reps": 10
    }},
    {{
      "type": "cardio",
      "exercise": "running",
      "duration": 30,
      "distance": 3.0
    }}
  ]
}}

Only include keys that apply. Don't add nulls. Do not explain anything. Only return valid JSON.

Workout: "{text}"
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that formats workout entries into strict JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )
    return response.choices[0].message.content
