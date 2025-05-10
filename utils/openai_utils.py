import json
from openai import OpenAI

client = OpenAI()


# noinspection PyTypeChecker
def parse_workout(text):
    prompt = f"""
You are a fitness assistant. A user will describe their workout in natural language.
Convert it into a strict JSON object with only the fields needed.

### Required JSON structure:
Always return a dictionary with exactly two keys:
- "entries": a list of workout items
- "notes": a general string (can be empty if nothing general to say)

NEVER return just a list. NEVER omit the top-level "entries" and "notes" keys.

### Example output:

{{
  "entries": [
    {{
      "type": "strength",
      "exercise": "squats",
      "sets": 3,
      "reps": 10,
      "notes": "Focused on depth and form"
    }},
    {{
      "type": "cardio",
      "exercise": "running",
      "duration": 30,
      "distance": 3.0,
      "notes": "Felt good, ran outside"
    }}
  ],
  "notes": "Overall felt tired due to poor sleep."
}}

### Rules:
- Only include relevant keys. Do not include null, empty strings, or empty arrays.
- Entry-level `notes` are for per-exercise comments.
- Top-level `notes` are general reflections about the workout overall.
- Do NOT return explanations. Only return valid, parsable JSON.

### Input:
{text}
"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that formats workout entries into strict JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    content = response.choices[0].message.content
    return json.loads(content)
