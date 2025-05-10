from flask import Blueprint, jsonify
from sqlalchemy import text
from init import db

progress_bp = Blueprint("progress", __name__)

@progress_bp.route("/api/progress/cardio")
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

@progress_bp.route("/api/progress/cardio/<exercise>")
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

@progress_bp.route("/api/progress/strength/<exercise>")
def strength_progress(exercise):
    results = db.session.execute(text("""
        SELECT ws.date,
               we.sets * we.reps AS volume,
               we.weight AS max_weight
        FROM workout_entry we
        JOIN workout_session ws ON ws.id = we.session_id
        WHERE we.type = 'strength' AND LOWER(we.exercise) = :exercise
        GROUP BY ws.date, we.weight
        ORDER BY ws.date
    """), {"exercise": exercise.lower()}).fetchall()

    return jsonify([
        {"date": r[0], "volume": r[1], "max_weight": r[2]} for r in results
    ])
