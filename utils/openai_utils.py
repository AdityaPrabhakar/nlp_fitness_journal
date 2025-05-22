import json
from openai import OpenAI
from datetime import date

client = OpenAI()

# noinspection PyTypeChecker
def parse_workout(text):
    today = date.today().isoformat()

    prompt = f"""
    You are a fitness assistant. A user will describe their workout in natural language.
    Convert it into a strict JSON object with only the fields needed, using **American units only**.

    ### Context:
    Today's date is {today}. Use this to resolve any relative dates like "yesterday", "last week", "on Monday", etc.

    ### Units Standardization Rules:
    - All distances must be in **miles**. Convert from kilometers (1 km = 0.621371 miles).
    - All weights must be in **pounds (lbs)**. Convert from kilograms (1 kg = 2.20462 lbs).
    - All durations should be in **minutes**. Handle terms like "half an hour" as 30.
    - If no units are provided (e.g. "ran 2"), assume American units (e.g., miles for distance, lbs for weight).
    - Strip all units in the final output and return numeric values only.

    ### Required JSON structure:
    Always return a dictionary with the following keys:
    - "date": ISO format date string (YYYY-MM-DD), **only if a specific or relative date is mentioned** in the text
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
        - "reps": number of reps (if not mentioned, omit or set to null)
        - "weight": numeric value only (standardized to pounds)

    For cardio, include:
    - "duration": numeric value only (in minutes)
    - "distance": numeric value only (in miles)

    ### Normalization:
    - Normalize common exercise name typos and variations.
      For example:
        - "dumbell press" → "dumbbell press"
        - "benchpress" → "bench press"
        - "pushups" → "push-ups"
        - "dead lift" → "deadlift"
        - Ensure consistency across entries even with different spellings.

    ### Example output:

    {{
      "date": "2024-05-11",
      "entries": [
        {{
          "type": "strength",
          "exercise": "bench press",
          "sets_details": [
            {{ "set_number": 1, "reps": 8, "weight": 135 }},
            {{ "set_number": 2, "reps": 6, "weight": 155 }}
          ],
          "notes": "Felt strong"
        }},
        {{
          "type": "cardio",
          "exercise": "running",
          "duration": 30,
          "distance": 3.1
        }}
      ],
      "notes": "Solid training day."
    }}

    ### Rules:
    - Normalize common exercise name typos and variations (see above).
    - Use the provided date context to convert relative dates into absolute ones.
    - Only include "date" if a specific or relative date is mentioned.
    - Do not guess a date if none is mentioned — just omit the "date" key.
    - Always convert metric units to American units as instructed.
    - Only include relevant keys. Do not include null, empty strings, or empty arrays.
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
