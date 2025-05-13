from flask import Blueprint, jsonify
from sqlalchemy import text
from init import db

progress_bp = Blueprint("progress", __name__)

@progress_bp.route("/api/progress/cardio")
def cardio_progress():
    results = db.session.execute(text("""
        SELECT ws.date,
               SUM(ce.distance) AS distance,
               SUM(ce.duration) AS duration
        FROM cardio_entry ce
        JOIN workout_entry we ON we.id = ce.entry_id
        JOIN workout_session ws ON ws.id = we.session_id
        GROUP BY ws.date
        ORDER BY ws.date
    """)).fetchall()

    return jsonify([
        {"date": r[0], "distance": r[1], "duration": r[2]} for r in results
    ])

@progress_bp.route("/api/progress/cardio/<exercise>")
def cardio_progress_by_exercise(exercise):
    results = db.session.execute(text("""
        SELECT ws.date,
               SUM(ce.distance) AS distance,
               SUM(ce.duration) AS duration
        FROM cardio_entry ce
        JOIN workout_entry we ON we.id = ce.entry_id
        JOIN workout_session ws ON ws.id = we.session_id
        WHERE LOWER(we.exercise) = :exercise
        GROUP BY ws.date
        ORDER BY ws.date
    """), {"exercise": exercise.lower()}).fetchall()

    return jsonify([
        {"date": r[0], "distance": r[1], "duration": r[2]} for r in results
    ])

@progress_bp.route("/api/progress/strength/<exercise>")
def strength_progress(exercise):
    results = db.session.execute(text("""
        SELECT
            ws.date,
            SUM(se.reps * COALESCE(se.weight, 0)) AS volume,
            MAX(se.weight) AS max_weight
        FROM strength_entry se
        JOIN workout_entry we ON we.id = se.entry_id
        JOIN workout_session ws ON ws.id = we.session_id
        WHERE LOWER(we.exercise) = :exercise
        GROUP BY ws.date
        ORDER BY ws.date
    """), {"exercise": exercise.lower()}).fetchall()

    return jsonify([
        {"date": r[0], "volume": r[1], "max_weight": r[2]} for r in results
    ])
