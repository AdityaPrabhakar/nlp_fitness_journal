from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import WorkoutEntry, WorkoutSession, StrengthEntry, CardioEntry
from init import db

exercise_bp = Blueprint("exercise", __name__)

@exercise_bp.route("/api/exercises/<exercise_type>")
@jwt_required()
def get_exercises_by_type(exercise_type):
    if exercise_type not in ["cardio", "strength"]:
        return jsonify([]), 400

    user_id = get_jwt_identity()

    exercises = (
        db.session.query(WorkoutEntry.exercise)
        .join(WorkoutSession)  # Join WorkoutEntry.session (WorkoutSession)
        .filter(
            WorkoutEntry.type == exercise_type,
            WorkoutSession.user_id == user_id
        )
        .distinct()
        .all()
    )

    return jsonify([e[0] for e in exercises])

@exercise_bp.route("/api/exercise-data/<string:exercise_name>")
@jwt_required()
def get_exercise_data(exercise_name):
    user_id = get_jwt_identity()

    # Fetch all strength entries for the given exercise and user
    strength_results = (
        db.session.query(StrengthEntry, WorkoutSession.date)
        .join(WorkoutEntry, StrengthEntry.entry_id == WorkoutEntry.id)
        .join(WorkoutSession, WorkoutEntry.session_id == WorkoutSession.id)
        .filter(
            WorkoutEntry.exercise == exercise_name,
            WorkoutSession.user_id == user_id
        )
        .all()
    )

    # Fetch all cardio entries for the given exercise and user
    cardio_results = (
        db.session.query(CardioEntry, WorkoutSession.date)
        .join(WorkoutEntry, CardioEntry.entry_id == WorkoutEntry.id)
        .join(WorkoutSession, WorkoutEntry.session_id == WorkoutSession.id)
        .filter(
            WorkoutEntry.exercise == exercise_name,
            WorkoutSession.user_id == user_id
        )
        .all()
    )

    # Format data
    data = []

    for s, date in strength_results:
        data.append({
            "type": "strength",
            "date": date,
            "reps": s.reps,
            "weight": s.weight,
            "sets": 1,  # assume 1 per entry unless you're aggregating
        })

    for c, date in cardio_results:
        data.append({
            "type": "cardio",
            "date": date,
            "duration_minutes": c.duration,
            "distance": c.distance,
        })

    # Sort chronologically
    data.sort(key=lambda x: x["date"])
    return jsonify(data)