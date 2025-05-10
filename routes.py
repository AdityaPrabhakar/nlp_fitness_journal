import json
from flask import request, render_template, redirect, jsonify
from datetime import datetime
from models import db, WorkoutSession, WorkoutEntry
from openai_utils import parse_workout
from sqlalchemy import text
from flask import current_app as app

# Main page to log workout sessions
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
                reps=item.get("reps"),
                weight=item.get("weight")
            )
            db.session.add(entry)

        db.session.commit()
        return redirect("/")

    # Fetch distinct exercises for both cardio and strength
    cardio_exercises = db.session.query(WorkoutEntry.exercise).filter(WorkoutEntry.type == 'cardio').distinct().all()
    strength_exercises = db.session.query(WorkoutEntry.exercise).filter(WorkoutEntry.type == 'strength').distinct().all()

    # Flatten the results from tuples to a list of strings
    cardio_exercises = [e[0] for e in cardio_exercises]
    strength_exercises = [e[0] for e in strength_exercises]

    sessions = WorkoutSession.query.order_by(WorkoutSession.id.desc()).all()
    return render_template("index.html", sessions=sessions, cardio_exercises=cardio_exercises, strength_exercises=strength_exercises)


# Generic cardio progress (summed over all cardio exercises)
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


# Cardio progress for a specific exercise (e.g., running, cycling)
@app.route("/api/progress/cardio/<exercise>")
def cardio_progress_by_exercise(exercise):
    results = db.session.execute(text("""
        SELECT ws.date,
               SUM(we.distance) AS distance,
               SUM(we.duration) AS duration
        FROM workout_entry we
        JOIN workout_session ws ON ws.id = we.session_id
        WHERE we.type = 'cardio' AND we.exercise = :exercise
        GROUP BY ws.date
        ORDER BY ws.date
    """), {"exercise": exercise}).fetchall()

    return jsonify([
        {"date": r[0], "distance": r[1], "duration": r[2]} for r in results
    ])

# Strength progress for a specific exercise (e.g., pushups, squats)
@app.route("/api/progress/strength/<exercise>")
def strength_progress(exercise):
    results = db.session.execute(text("""
        SELECT ws.date,
               we.sets * we.reps AS volume,
               we.weight AS max_weight
        FROM workout_entry we
        JOIN workout_session ws ON ws.id = we.session_id
        WHERE we.type = 'strength' AND LOWER(we.exercise) = :exercise
        GROUP BY ws.date, we.weight  -- Group by both date and weight
        ORDER BY ws.date
    """), {"exercise": exercise.lower()}).fetchall()

    return jsonify([
        {"date": r[0], "volume": r[1], "max_weight": r[2]} for r in results
    ])




# Endpoint to fetch exercises based on type (cardio or strength)
@app.route("/api/exercises/<exercise_type>")
def get_exercises_by_type(exercise_type):
    valid_types = ["cardio", "strength"]
    if exercise_type not in valid_types:
        return jsonify([]), 400

    exercises = (
        db.session.query(WorkoutEntry.exercise)
        .filter(WorkoutEntry.type == exercise_type)
        .distinct()
        .all()
    )
    return jsonify([e[0] for e in exercises])
