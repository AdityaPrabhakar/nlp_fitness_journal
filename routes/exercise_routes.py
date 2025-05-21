from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import WorkoutEntry
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
        .filter_by(type=exercise_type, user_id=user_id)
        .distinct()
        .all()
    )

    return jsonify([e[0] for e in exercises])
