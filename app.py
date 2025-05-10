from flask import Flask, render_template, request, redirect
from models import db, WorkoutSession, WorkoutEntry
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
import json

# Load .env variables
load_dotenv()
client = OpenAI()

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()

# Function to call OpenAI and structure the workout
# noinspection PyTypeChecker
def parse_workout(text):
    prompt = f"""
    You are a fitness assistant. A user will describe their workout in natural language.
    Your job is to convert it into a structured JSON object, following this exact format:
    
    {{
      "entries": [
        {{
          "type": "strength",
          "exercise": "push-ups",
          "sets": 3,
          "reps": 10
        }},
        {{
          "type": "cardio",
          "exercise": "running",
          "distance_miles": 2
        }}
      ]
    }}
    
    Only include keys that are relevant. Do not explain anything. Only return JSON.
    
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
                sets=item.get("sets"),
                reps=item.get("reps")
            )
            db.session.add(entry)

        db.session.commit()
        return redirect("/")

    sessions = WorkoutSession.query.order_by(WorkoutSession.id.desc()).all()
    return render_template("index.html", sessions=sessions)

if __name__ == "__main__":
    app.run(debug=True)
