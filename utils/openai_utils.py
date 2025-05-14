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

    ### Entry format:
    Each workout entry must have:
    - "type": either "strength", "cardio", or another clearly inferred category
    - "exercise": name of the exercise (e.g. "bench press")
    - "notes": per-exercise notes if provided (optional)

    For strength training, include:
    - "sets_details": a list of sets, each with:
        - "set_number": the set index (1-based)
        - "reps": number of reps
        - "weight": weight used (if mentioned; otherwise omit)

    For cardio, include:
    - "duration": in minutes (if provided)
    - "distance": in miles or km (if provided)

    ### Example output:

    {{
      "entries": [
        {{
          "type": "strength",
          "exercise": "bench press",
          "sets_details": [
            {{ "set_number": 1, "reps": 8, "weight": 135 }},
            {{ "set_number": 2, "reps": 6, "weight": 155 }},
            {{ "set_number": 3, "reps": 6, "weight": 155 }}
          ],
          "notes": "Felt strong today"
        }},
        {{
          "type": "cardio",
          "exercise": "running",
          "duration": 30,
          "distance": 3.0,
          "notes": "Jogged in the park"
        }}
      ],
      "notes": "Solid session overall."
    }}

    ### Rules:
    - Only include relevant keys. Do not include null, empty strings, or empty arrays.
    - Only include actual workouts — completed activities, not future intentions.
    - Top-level "notes" should summarize the entire workout.
    - Do NOT return explanations. Only return valid, parsable JSON.

    ### Input:
    {text}
    """

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that formats workout entries into strict JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    content = response.choices[0].message.content
    return json.loads(content)

def clean_entry(entry):
    """Fixes and enriches a single workout entry."""
    if 'reps' in entry and ('sets' not in entry or not entry['sets']):
        entry['sets'] = 1

    # Calculate volume if applicable
    if 'reps' in entry and 'sets' in entry:
        entry['volume'] = entry['reps'] * entry['sets']

    return entry


def clean_entries(entries):
    """Cleans and normalizes a list of entries."""
    return [clean_entry(entry) for entry in entries]


# noinspection PyTypeChecker
def parse_goals(text):
    prompt = f"""
You are a fitness assistant helping users set workout goals.
A user may describe a goal they want to accomplish (e.g. "run 50 miles this month" or "increase my bench press to 200 lbs").
Extract these goals and structure them in JSON format.

### Required JSON structure:
Always return an object with a "goals" key (a list). If there are no goals, return an empty list.

Each goal must have:
- "exercise": the name of the exercise
- "start_date": ISO format (e.g. "2025-05-01") — if not stated, default to today
- "end_date": ISO format — try to infer from the text (e.g. "by end of month" → last day of this month)
- "targets": a list of target objects. Each has:
    - "target_field": one of ["sets", "reps", "weight", "distance", "duration", "volume"]
    - "target_value": a float

Never include nulls or explanations.

### Example:

{{
  "goals": [
    {{
      "exercise": "running",
      "start_date": "2025-05-01",
      "end_date": "2025-05-31",
      "targets": [
        {{
          "target_field": "distance",
          "target_value": 50
        }},
        {{
          "target_field": "duration",
          "target_value": 300
        }}
      ]
    }},
    {{
      "exercise": "bench press",
      "start_date": "2025-05-01",
      "end_date": "2025-06-15",
      "targets": [
        {{
          "target_field": "weight",
          "target_value": 200
        }}
      ]
    }}
  ]
}}

### Input:
{text}
"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You extract structured fitness goals from journal text."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3
    )

    content = response.choices[0].message.content
    return json.loads(content)
