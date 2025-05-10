from flask import Flask, render_template, request, redirect, jsonify
from sqlalchemy import text
from models import db, WorkoutSession, WorkoutEntry
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
import json
import os


# Load .env variables
load_dotenv()
client = OpenAI()

ENV = os.getenv("ENV", "production")

# Initialize Flask app
app = Flask(__name__)
if ENV == "testing":
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


def seed_test_data():
    print("Seeding test data...")

    # Clear existing
    db.session.query(WorkoutEntry).delete()
    db.session.query(WorkoutSession).delete()
    db.session.commit()

    sample_sessions = [
        ("2025-05-01", "Ran 3 miles in 30 minutes, did 3 sets of 10 pushups."),
        ("2025-05-02", "Cycled for 45 minutes, 4 sets of 12 squats."),
        ("2025-05-03", "5 miles running in 50 minutes, 3 sets of 8 pullups."),
        ("2025-05-04", "Jump rope for 20 minutes, 5 sets of 5 deadlifts.")
    ]

    for date, raw_text in sample_sessions:
        session = WorkoutSession(date=date, raw_text=raw_text)
        db.session.add(session)
        db.session.commit()

        # Simulate parsed entries
        if "ran" in raw_text.lower() or "running" in raw_text.lower():
            db.session.add(WorkoutEntry(
                session_id=session.id,
                type="cardio",
                exercise="running",
                distance=3.0 if "3 miles" in raw_text else 5.0,
                duration=30 if "30 minutes" in raw_text else 50
            ))
        if "cycled" in raw_text.lower():
            db.session.add(WorkoutEntry(
                session_id=session.id,
                type="cardio",
                exercise="cycling",
                duration=45
            ))
        if "jump rope" in raw_text.lower():
            db.session.add(WorkoutEntry(
                session_id=session.id,
                type="cardio",
                exercise="jump rope",
                duration=20
            ))

        if "pushups" in raw_text:
            db.session.add(WorkoutEntry(
                session_id=session.id,
                type="strength",
                exercise="pushups",
                sets=3,
                reps=10
            ))
        if "squats" in raw_text:
            db.session.add(WorkoutEntry(
                session_id=session.id,
                type="strength",
                exercise="squats",
                sets=4,
                reps=12
            ))
        if "pullups" in raw_text:
            db.session.add(WorkoutEntry(
                session_id=session.id,
                type="strength",
                exercise="pullups",
                sets=3,
                reps=8
            ))
        if "deadlifts" in raw_text:
            db.session.add(WorkoutEntry(
                session_id=session.id,
                type="strength",
                exercise="deadlifts",
                sets=5,
                reps=5
            ))

    db.session.commit()


with app.app_context():
    db.create_all()
    if ENV == "testing":
        seed_test_data()

# Function to call OpenAI and structure the workout
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
            {
                "role": "system",
                "content": "You are a helpful assistant that formats workout entries into strict JSON for logging purposes."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.3
    )

    return response.choices[0].message.content


# Route for homepage
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        raw_text = request.form["entry"]
        now = datetime.now().strftime("%Y-%m-%d")

        try:
            structured_response = parse_workout(raw_text)
            parsed = json.loads(structured_response)
        except Exception as e:
            print("Error parsing:", e)
            parsed = {"entries": []}

        # Save session
        session = WorkoutSession(date=now, raw_text=raw_text)
        db.session.add(session)
        db.session.commit()

        # Save entries
        for item in parsed.get("entries", []):
            entry = WorkoutEntry(
                session_id=session.id,
                type=item.get("type"),
                exercise=item.get("exercise"),
                duration=item.get("duration"),
                distance=item.get("distance"),
                sets=item.get("sets"),
                reps=item.get("reps")
            )
            db.session.add(entry)

        db.session.commit()
        return redirect("/")

    sessions = WorkoutSession.query.order_by(WorkoutSession.id.desc()).all()
    return render_template("index.html", sessions=sessions)

@app.route("/api/progress/cardio")
def cardio_progress():
    results = db.session.execute(text("""
        SELECT ws.date,
               SUM(we.distance) AS total_distance,
               SUM(we.duration) AS total_duration
        FROM workout_entry we
        JOIN workout_session ws ON ws.id = we.session_id
        WHERE we.type = 'cardio'
        GROUP BY ws.date
        ORDER BY ws.date
    """)).fetchall()

    return jsonify([
        {
            "date": row[0],
            "distance": round(row[1], 2) if row[1] is not None else None,
            "duration": round(row[2], 2) if row[2] is not None else None
        } for row in results
    ])


if __name__ == "__main__":
    app.run(debug=True)
