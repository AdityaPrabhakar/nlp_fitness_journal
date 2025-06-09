import json

import pytz
from openai import OpenAI
from datetime import date, datetime

client = OpenAI()


# noinspection PyTypeChecker
def parse_workout_and_goals(text, today_override=None):
    today = today_override or datetime.now().date().isoformat()

    prompt = f"""
    You are a fitness assistant. A user will describe their workout and goals in natural language.
    Convert it into a strict JSON object that matches the required schema. Use **American units only**.

    ### Context:
    Today's date is {today}. Use this to resolve relative time expressions like "yesterday", "next week", "starting Monday", etc.

    ### Relative Time Rules:
    - Use today’s date ({today}) to compute `start_date` and `end_date` when relative expressions are used
    - For phrases like:
      - "this week": `start_date = today`, `end_date = 7 days after today`
      - "next week": `start_date = the next Monday`, `end_date = the next Sunday`
      - "this month": `start_date = today`, `end_date = 30 days after today`
      - "in two weeks": `start_date = today`, `end_date = 14 days after today`
      - "by Friday": `start_date = today`, `end_date = the upcoming Friday`
    - If the time range is ambiguous but says something like “this week” or “this month”, infer a matching `end_date` by default

    ### Intent Detection Rules:
    - Treat sentences like “I want to…”, “I plan to…”, “I aim to…”, “I'd like to…”, “My goal is…”, “I’m hoping to…” as clear goal declarations
    - Convert any of these statements into a structured goal, even if no workout was logged
    - Default `start_date` to today if not specified

    ### Required Output Format:
    Return a dictionary with the following keys:
    - "date": ISO format (YYYY-MM-DD), only if the text includes a specific or relative date
    - "entries": list of past workout entries
    - "notes": general string (can be empty)
    - "goals": list of structured goals (see schema below)

    ### Workout Entry Format:
    Each entry must include:
    - "type": "strength", "cardio", or another
    - "exercise": normalized name (e.g. "bench press", "running")
    - "notes": optional per-exercise notes
    - For strength:
      - "sets_details": list of sets with "set_number", "reps", and "weight" (numeric, lbs only)
      - Only include "weight" if the user specified it
    - For cardio:
      - "duration": in minutes
      - "distance": in miles
      - "pace": optional (minutes per mile)

    ### Goal Format (match this SQL schema exactly):
    Each goal must include:
    - "name": short title like "Bench 225" or "Run 10 miles"
    - "description": detailed description (optional)
    - "start_date": ISO format string
    - "end_date": optional ISO string (for longer goals)
    - "goal_type": one of: "single_session" or "aggregate"
    - "exercise_type": one of: "strength", "cardio", "general"
    - "exercise_name": optional, e.g. "bench press"
    - "targets": list of objects, each with:
      - "target_metric": one of: "reps", "sets", "distance", "duration", "weight", "sessions", "pace"
      - "target_value": numeric only (American units)
      - Only include one of "duration" or "pace" per target. If "pace" is used, omit duration and distance.

    ### Goal Type Guidelines:
    - If a goal mentions repeating something "daily", "weekly", or similar, assume it means "in one day" or "in one week"
    - If a goal mentions "tomorrow", assume it means "by the end of tomorrow" and ensure an end_date is set
    - Default to `goal_type: "single_session"` unless **one of the following is clearly true**:
      - The user explicitly states a **total or combined amount over time**, using words like “total”, “combined”, “cumulative”, or similar
      - The goal is **general or schedule-based**, such as “do cardio 5 times” or “work out 3 days a week”
    - Use `goal_type: "aggregate"` **only** for cumulative goals across multiple sessions, and **only** when the user clearly communicates this intent through specific language
    - Use `exercise_type: "general"` for non-exercise-specific goals such as “stay active every day” or “train 4 times a week”
    - If a user says “run X miles in Y minutes”, convert it into a **pace-based goal** using:  
      `pace = duration / distance` (in minutes per mile).  
      In this case:
        - Include both `pace` and `distance` targets  
        - Do NOT include `duration`


    ### Normalization Rules:
    - Convert all distances to miles (1 km = 0.621371 miles)
    - Convert all weights to pounds (1 kg = 2.20462 lbs)
    - Durations must be in minutes
    - Remove units from final output
    
    ### Exercise Normalization Guardrails:
    - Normalize exercise names to a consistent form used across the dataset or app UI
    - Common corrections:
      - "pullup", "pull-up" → "pull-ups"
      - "pushup", "push-up" → "push-ups"
      - "benchpress" → "bench press"
      - "dumbell" → "dumbbell"
      - Singular/plural variants like "pull-up" and "pull-ups" must resolve to **"pull-ups"**
    - Do NOT create variations such as "pull-up" and "pullups" as separate entries — they must all map to one canonical name (e.g., "pull-ups")
    - Use consistent casing and hyphenation (e.g. always "push-ups", not "Pushups" or "Push ups")
    - Apply these corrections **in both workout entries and goals**

    ### Rules:
    - Do NOT include goals inside the "entries" section
    - Only include keys that are relevant — do not include null or empty values
    - Do NOT guess "date" unless explicitly mentioned
    - Do NOT output extra explanation, only valid parsable JSON
    - If no goal name is given, generate a short title based on the user's phrasing (e.g., "Run this week", "Bench 225")

    ### Example Output:

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
          "notes": "felt strong"
        }},
        {{
          "type": "cardio",
          "exercise": "running",
          "duration": 30,
          "distance": 3.1
        }}
      ],
      "notes": "solid day",
      "goals": [
        {{
          "name": "Bench 225",
          "description": "Try 225 lbs bench press next week",
          "start_date": "2024-05-18",
          "goal_type": "single_session",
          "exercise_type": "strength",
          "exercise_name": "bench press",
          "targets": [
            {{ "target_metric": "weight", "target_value": 225 }}
          ]
        }},
        {{
          "name": "Run 10 miles this week",
          "description": "Run at least 10 miles in one week",
          "start_date": "2024-05-13",
          "goal_type": "aggregate",
          "exercise_type": "cardio",
          "exercise_name": "running",
          "targets": [
            {{ "target_metric": "distance", "target_value": 10 }}
          ]
        }},
        {{
          "name": "Sub-8:00 pace 3-miler",
          "description": "Run 3 miles in 24 minutes (8:00/mile pace)",
          "start_date": "2024-06-02",
          "goal_type": "single_session",
          "exercise_type": "cardio",
          "exercise_name": "running",
          "targets": [
            {{ "target_metric": "pace", "target_value": 8.0 }}
          ]
        }}
      ]
    }}

    ### Input:
    {text}
    """

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant that formats workouts and goals into strict JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3
    )

    content = response.choices[0].message.content
    return json.loads(content)




def clean_entry(entry):
    """Fixes and enriches a single workout entry."""
    entry_type = entry.get('type')

    if entry_type == 'strength':
        # Default sets = 1 if reps are present but sets missing
        if 'reps' in entry and ('sets' not in entry or not entry['sets']):
            entry['sets'] = 1

        # Calculate volume
        if 'reps' in entry and 'sets' in entry:
            entry['volume'] = entry['reps'] * entry['sets']

    elif entry_type == 'cardio':
        # Infer pace if distance and duration are provided
        distance = entry.get("distance")
        duration = entry.get("duration")

        if distance and duration and distance > 0:
            entry["pace"] = duration / distance  # pace in min/mi or min/km

        # You could also infer duration if pace and distance are known
        if "pace" in entry and not entry.get("duration") and distance:
            entry["duration"] = entry["pace"] * distance

        # Or infer distance if duration and pace are known
        if "pace" in entry and not entry.get("distance") and duration:
            entry["distance"] = duration / entry["pace"]

    return entry



def clean_entries(entries):
    """Cleans and normalizes a list of entries."""
    return [clean_entry(entry) for entry in entries]



def recommend_followup_set(exercise_name, sets_details, goal="increase 1RM slightly"):
    """
    Recommends a follow-up set scheme for a strength exercise using OpenAI.
    Ensures small progression in either 1RM or total volume (or both).
    """
    from collections import defaultdict
    import json

    valid_sets = [s for s in sets_details if 'reps' in s and 'set_number' in s and 'session_id' in s]
    has_weights = any("weight" in s and s["weight"] and s["weight"] > 0 for s in valid_sets)

    session_counts = defaultdict(int)
    for s in valid_sets:
        session_counts[s["session_id"]] += 1

    num_sessions = len(session_counts)
    total_sets = len(valid_sets)
    avg_sets = round(total_sets / num_sessions) if num_sessions > 0 else total_sets

    if has_weights:
        total_volume = sum(
            s["reps"] * s["weight"]
            for s in valid_sets
            if isinstance(s.get("weight"), (int, float)) and s["weight"] > 0
        )
        peak_1rm = max(
            s["weight"] / (1.0278 - 0.0278 * s["reps"])  # Epley formula
            for s in valid_sets
            if s["reps"] > 0 and s["weight"] > 0
        )
    else:
        total_volume = sum(s["reps"] for s in valid_sets)
        peak_1rm = None  # Not used

    formatted_sets = "\n".join(
        f"- Set {s['set_number']} (Session {s['session_id']}): {s['reps']} reps" +
        (f" at {s['weight']} lbs" if has_weights else "")
        for s in valid_sets
    )

    guidelines = f"""
Guidelines:
- Keep total sets within ±1 of the average session count ({avg_sets} sets).
- You MUST ensure at least one of these two conditions is met:
  1. Total volume (reps × weight) increases slightly (~1–3%) compared to recent average (≈ {total_volume}).
  2. Peak intensity (1RM estimate) increases slightly (~1–3%) from last best (≈ {round(peak_1rm, 1) if peak_1rm else 'N/A'}).
- Do NOT repeat a plateaued scheme (e.g. if the user did 45 push-ups, do NOT just suggest 3×15).
- Avoid proposing multiple very large sets that would double total volume.
- Recommend weights ONLY in 5 lb increments (e.g., 185, 190).
- Avoid spiking both reps and weight in the same set.
- Small, measurable progress is required.

Return ONLY strict JSON, exactly in this format:

{{
  "recommended_sets": [
    {{ "set_number": 1, "reps": 10, "weight": 185 }},
    {{ "set_number": 2, "reps": 8, "weight": 190 }},
    {{ "set_number": 3, "reps": 6, "weight": 195 }}
  ],
  "rationale": "Brief reasoning here."
}}
""" if has_weights else f"""
Guidelines:
- Keep total sets within ±1 of the average session count ({avg_sets} sets).
- You MUST ensure at least one of the following:
  1. Slight increase (~1–3%) in total volume compared to recent average (≈ {total_volume} reps).
  2. Increased density (more reps in fewer sets or in same time).
- Do NOT repeat an identical rep scheme if it shows no progression (e.g. repeating 45 pushups as 3×15 is not valid).
- Favor small, realistic progress in total workload.
- Do NOT include weights unless they appear in the original data.

Return ONLY strict JSON, exactly in this format:

{{
  "recommended_sets": [
    {{ "set_number": 1, "reps": 18 }},
    {{ "set_number": 2, "reps": 15 }},
    {{ "set_number": 3, "reps": 12 }}
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
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that provides realistic strength training set recommendations."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
    )

    content = response.choices[0].message.content
    return json.loads(content)

def recommend_followup_cardio(exercise_name, session_data, goal="improve endurance slightly"):
    import json

    # Detect available metrics
    has_distance = any("distance" in s and s["distance"] for s in session_data)
    has_duration = any("duration" in s and s["duration"] for s in session_data)
    has_pace = any("pace" in s and s["pace"] for s in session_data)

    formatted_sessions = "\n".join(
        f"- Session {s['session_id']} on {s['date']}:"
        + (f" {s['distance']} miles" if has_distance and s.get("distance") else "")
        + (f", {s['duration']} min" if has_duration and s.get("duration") else "")
        + (f", {s['pace']} min/mile" if has_pace and s.get("pace") else "")
        for s in session_data
    )

    guidelines = f"""
Guidelines:
- Recommend a realistic 1–5% improvement in each field independently.
- Return a SEPARATE recommendation for each metric you find in the user's history.
- Do NOT include any field in a recommendation if that field wasn't tracked before.
- Do NOT combine metrics in a single recommendation.
- Make sure each recommendation improves ONLY ONE FIELD AT A TIME.

Return valid JSON in this format:

{{
  "recommendations": [
    {{
      "improved_metric": "distance",
      "recommended_session": {{
        "distance_miles": <value>
      }},
      "rationale": "Why this small distance improvement makes sense."
    }},
    {{
      "improved_metric": "duration",
      "recommended_session": {{
        "duration_minutes": <value>
      }},
      "rationale": "Why this slight duration increase helps."
    }},
    {{
      "improved_metric": "pace",
      "recommended_session": {{
        "target_pace_min_per_mile": <value>
      }},
      "rationale": "Why adjusting pace could improve performance."
    }}
  ]
}}

Only include entries for supported metrics. No text outside the JSON object.
"""

    prompt = f"""
You are a cardio coach helping an intermediate user optimize their next training sessions by focusing on individual aspects of their workouts.

Exercise: {exercise_name}
Past sessions:
{formatted_sessions}

Goal: {goal}
{guidelines}
"""

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that gives intelligent cardio training suggestions."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
    )

    content = response.choices[0].message.content.strip()

    return json.loads(content)
