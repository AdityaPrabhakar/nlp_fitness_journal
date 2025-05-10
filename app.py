from flask import Flask, render_template, request, redirect
from models import db, WorkoutEntry
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

        try:
            structured_response = parse_workout(raw_text)
        except Exception as e:
            structured_response = json.dumps({"error": str(e)})

        entry = WorkoutEntry(
            date=datetime.now().strftime("%Y-%m-%d"),
            description=raw_text,
            structured_data=structured_response
        )
        db.session.add(entry)
        db.session.commit()
        return redirect("/")

    entries = WorkoutEntry.query.order_by(WorkoutEntry.id.desc()).all()

    # Parse JSON for template use
    for entry in entries:
        try:
            entry.parsed_data = json.loads(entry.structured_data)
        except:
            entry.parsed_data = {"error": "Invalid JSON"}

    return render_template("index.html", entries=entries)

if __name__ == "__main__":
    app.run(debug=True)
