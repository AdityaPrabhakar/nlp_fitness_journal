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


# noinspection PyTypeChecker
def recommend_followup_set(exercise_name, sets_details, goal="increase 1RM slightly"):
    """
    Recommends a follow-up set scheme for a strength exercise using OpenAI.
    Automatically infers average sets per session using `session_id` in `sets_details`.
    Skips weight recommendations for bodyweight-only movements.
    """
    from collections import defaultdict

    valid_sets = [s for s in sets_details if 'reps' in s and 'set_number' in s and 'session_id' in s]
    has_weights = any("weight" in s and s["weight"] > 0 for s in valid_sets)

    session_counts = defaultdict(int)
    for s in valid_sets:
        session_counts[s["session_id"]] += 1

    num_sessions = len(session_counts)
    total_sets = len(valid_sets)
    avg_sets = round(total_sets / num_sessions) if num_sessions > 0 else total_sets

    if has_weights:
        formatted_sets = "\n".join(
            f"- Set {s['set_number']} (Session {s['session_id']}): {s['reps']} reps at {s['weight']} lbs"
            for s in valid_sets if "weight" in s
        )
        guidelines = f"""
Guidelines:
- Keep total sets within ±1 of the average session count ({avg_sets} sets).
- Recommend weights ONLY in increments of 5 lbs (e.g., 185, 190, 195 — not 187 or 193).
- Use realistic progression: keep volume similar unless the goal requests more.
- You may vary reps/weight per set, but avoid spikes in both simultaneously.
- Target a ~1–3% increase in intensity if aiming for strength progression.
- Do NOT overreach or propose unrealistic jumps in load or volume.

Return ONLY strict JSON, exactly in this format:

{{
  "recommended_sets": [
    {{ "set_number": 1, "reps": 5, "weight": 190 }},
    {{ "set_number": 2, "reps": 4, "weight": 195 }},
    {{ "set_number": 3, "reps": 3, "weight": 200 }}
  ],
  "rationale": "Brief reasoning here."
}}
"""
    else:
        formatted_sets = "\n".join(
            f"- Set {s['set_number']} (Session {s['session_id']}): {s['reps']} reps"
            for s in valid_sets
        )
        guidelines = f"""
Guidelines:
- Keep total sets within ±1 of the average session count ({avg_sets} sets).
- Recommend realistic reps for bodyweight movements.
- Do NOT include weights or assume weighted variations unless explicitly shown in the sets.
- Favor slight progression in reps or density if aiming to improve.

Return ONLY strict JSON, exactly in this format:

{{
  "recommended_sets": [
    {{ "set_number": 1, "reps": 12 }},
    {{ "set_number": 2, "reps": 10 }},
    {{ "set_number": 3, "reps": 8 }}
  ],
  "rationale": "Brief reasoning here."
}}
"""

    prompt = f"""
You are a strength training coach helping an intermediate gym-goer. The user has completed:

Exercise: {exercise_name}
Performed sets:
{formatted_sets}

Goal: {goal}
{guidelines}

Do not include any text outside the JSON block.
    """

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that provides realistic strength training set recommendations."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3,
    )

    content = response.choices[0].message.content
    return json.loads(content)
