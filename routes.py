import json

from flask import request, render_template, redirect, jsonify
from datetime import datetime
from models import db, WorkoutSession, WorkoutEntry
from openai_utils import parse_workout
from sqlalchemy import text
from flask import current_app as app

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

        session = WorkoutSession(date=now, raw_text=raw_text)
        db.session.add(session)
        db.session.commit()

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
               SUM(we.distance) AS distance,
               SUM(we.duration) AS duration
        FROM workout_entry we
        JOIN workout_session ws ON ws.id = we.session_id
        WHERE we.type = 'cardio'
        GROUP BY ws.date
        ORDER BY ws.date
    """)).fetchall()

    return jsonify([
        {"date": r[0], "distance": r[1], "duration": r[2]} for r in results
    ])
