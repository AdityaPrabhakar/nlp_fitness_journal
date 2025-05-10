from flask import Blueprint, jsonify
from models import WorkoutEntry
from init import db

exercise_bp = Blueprint("exercise", __name__)

@exercise_bp.route("/api/exercises/<exercise_type>")
def get_exercises_by_type(exercise_type):
    if exercise_type not in ["cardio", "strength"]:
        return jsonify([]), 400

    exercises = db.session.query(WorkoutEntry.exercise).filter_by(type=exercise_type).distinct().all()
    return jsonify([e[0] for e in exercises])
