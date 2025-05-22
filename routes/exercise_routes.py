from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.orm import joinedload

from init import db
from models import WorkoutSession, WorkoutEntry, User
from utils import estimate_1rm  # Make sure this is your 1RM calculator

exercise_bp = Blueprint("exercise_bp", __name__)
DEFAULT_REPS = 1

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

@exercise_bp.route("/api/exercise-data/1rm-trend/<string:exercise>")
@jwt_required()
def strength_1rm_trend(exercise):
    user_id = get_jwt_identity()
    formula = request.args.get("formula", "epley")

    # Get the user's body weight
    user = db.session.get(User, user_id)
    if not user or not user.bodyweight:
        return jsonify({"error": "User bodyweight not available"}), 400

    bodyweight = user.bodyweight

    sessions = WorkoutSession.query.options(
        joinedload(WorkoutSession.entries).joinedload(WorkoutEntry.strength_entries)
    ).filter_by(user_id=user_id).order_by(WorkoutSession.date).all()

    trend = []
    for session in sessions:
        max_1rm = None
        for entry in session.entries:
            if entry.type != "strength" or entry.exercise.lower() != exercise.lower():
                continue
            for s in entry.strength_entries:
                reps = s.reps or DEFAULT_REPS
                # Use user's body weight if no weight is set
                weight = s.weight if s.weight and s.weight > 0 else bodyweight

                est_1rm = estimate_1rm(reps, weight, formula)
                if est_1rm is not None:
                    max_1rm = max(max_1rm or 0, est_1rm)
        if max_1rm:
            trend.append({
                "date": session.date,
                "estimated_1rm": round(max_1rm, 2)
            })

    return jsonify(trend)



@exercise_bp.route("/api/exercise-data/volume-trend/<string:exercise>")
@jwt_required()
def strength_volume_trend(exercise):
    user_id = get_jwt_identity()

    # Get the user's body weight
    user = db.session.get(User, user_id)
    if not user or not user.bodyweight:
        return jsonify({"error": "User bodyweight not available"}), 400

    bodyweight = user.bodyweight

    sessions = WorkoutSession.query.options(
        joinedload(WorkoutSession.entries).joinedload(WorkoutEntry.strength_entries)
    ).filter_by(user_id=user_id).order_by(WorkoutSession.date).all()

    trend = []
    for session in sessions:
        total_volume = 0
        for entry in session.entries:
            if entry.type != "strength" or entry.exercise.lower() != exercise.lower():
                continue
            for s in entry.strength_entries:
                reps = s.reps or DEFAULT_REPS
                # Use user's bodyweight if weight is not set
                weight = s.weight if s.weight and s.weight > 0 else bodyweight
                total_volume += reps * weight
        if total_volume > 0:
            trend.append({
                "date": session.date,
                "volume": round(total_volume, 2)
            })

    return jsonify(trend)





