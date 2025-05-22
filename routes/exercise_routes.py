from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta

from init import db
from models import WorkoutSession, WorkoutEntry, User, StrengthEntry
from utils import estimate_1rm

exercise_bp = Blueprint("exercise_bp", __name__)
DEFAULT_REPS = 1

# Utility to parse date range from query params
def get_date_range():
    try:
        start_str = request.args.get("start_date")
        end_str = request.args.get("end_date")
        end_date = datetime.strptime(end_str, "%Y-%m-%d").date() if end_str else datetime.today().date()
        start_date = datetime.strptime(start_str, "%Y-%m-%d").date() if start_str else end_date - timedelta(days=30)
        return start_date, end_date
    except Exception:
        return None, None

@exercise_bp.route("/api/exercises/<exercise_type>")
@jwt_required()
def get_exercises_by_type(exercise_type):
    if exercise_type not in ["cardio", "strength"]:
        return jsonify([]), 400

    user_id = get_jwt_identity()

    exercises = (
        db.session.query(WorkoutEntry.exercise)
        .join(WorkoutSession)
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

    user = db.session.get(User, user_id)
    if not user or not user.bodyweight:
        return jsonify({"error": "User bodyweight not available"}), 400

    bodyweight = user.bodyweight
    start_date, end_date = get_date_range()
    if not start_date or not end_date:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    # Make end date inclusive
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date + timedelta(days=1), datetime.min.time())

    sessions = WorkoutSession.query.options(
        joinedload(WorkoutSession.entries).joinedload(WorkoutEntry.strength_entries)
    ).filter(
        WorkoutSession.user_id == user_id,
        WorkoutSession.date >= start_dt,
        WorkoutSession.date < end_dt
    ).order_by(WorkoutSession.date).all()

    trend = []
    for session in sessions:
        max_1rm = None
        for entry in session.entries:
            if entry.type != "strength" or entry.exercise.lower() != exercise.lower():
                continue
            for s in entry.strength_entries:
                reps = s.reps or DEFAULT_REPS
                weight = s.weight if s.weight and s.weight > 0 else bodyweight
                est_1rm = estimate_1rm(reps, weight, formula)
                if est_1rm is not None:
                    max_1rm = max(max_1rm or 0, est_1rm)
        if max_1rm:
            trend.append({
                "session_id": session.id,
                "date": session.date.format(),
                "estimated_1rm": round(max_1rm, 2)
            })

    return jsonify(trend)


@exercise_bp.route("/api/exercise-data/volume-trend/<string:exercise>")
@jwt_required()
def strength_volume_trend(exercise):
    user_id = get_jwt_identity()

    user = db.session.get(User, user_id)
    if not user or not user.bodyweight:
        return jsonify({"error": "User bodyweight not available"}), 400

    bodyweight = user.bodyweight
    start_date, end_date = get_date_range()
    if not start_date or not end_date:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date + timedelta(days=1), datetime.min.time())  # inclusive

    sessions = WorkoutSession.query.options(
        joinedload(WorkoutSession.entries).joinedload(WorkoutEntry.strength_entries)
    ).filter(
        WorkoutSession.user_id == user_id,
        WorkoutSession.date >= start_dt,
        WorkoutSession.date < end_dt
    ).order_by(WorkoutSession.date).all()

    trend = []
    for session in sessions:
        total_volume = 0
        for entry in session.entries:
            if entry.type != "strength" or entry.exercise.lower() != exercise.lower():
                continue
            for s in entry.strength_entries:
                reps = s.reps or DEFAULT_REPS
                weight = s.weight if s.weight and s.weight > 0 else bodyweight
                total_volume += reps * weight
        if total_volume > 0:
            trend.append({
                "date": session.date,
                "volume": round(total_volume, 2)
            })

    return jsonify(trend)

@exercise_bp.route("/api/exercise-data/relative-intensity/<string:exercise_name>")
@jwt_required()
def get_relative_intensity(exercise_name):
    user_id = get_jwt_identity()
    formula = request.args.get("formula", "epley").lower()

    user = db.session.get(User, user_id)
    if not user or not user.bodyweight:
        return jsonify({"error": "User bodyweight not available"}), 400

    body_weight = user.bodyweight
    start_date, end_date = get_date_range()
    if not start_date or not end_date:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date + timedelta(days=1), datetime.min.time())  # inclusive

    sets = (
        db.session.query(StrengthEntry.reps, StrengthEntry.weight, WorkoutSession.date)
        .join(WorkoutEntry, StrengthEntry.entry_id == WorkoutEntry.id)
        .join(WorkoutSession, WorkoutEntry.session_id == WorkoutSession.id)
        .filter(
            WorkoutEntry.type == "strength",
            WorkoutEntry.exercise.ilike(exercise_name),
            WorkoutSession.user_id == user_id,
            WorkoutSession.date >= start_dt,
            WorkoutSession.date < end_dt
        )
        .order_by(WorkoutSession.date)
        .all()
    )

    # Calculate global max 1RM for the exercise
    max_1rm = 0
    parsed_sets = []
    for reps, weight, date in sets:
        reps = reps or DEFAULT_REPS
        weight = weight if weight and weight > 0 else body_weight
        est_1rm = estimate_1rm(reps, weight, formula=formula)
        if est_1rm:
            max_1rm = max(max_1rm, est_1rm)
            parsed_sets.append((reps, weight, date, est_1rm))

    if max_1rm == 0:
        return jsonify([])

    results = []
    for reps, weight, date, est_1rm in parsed_sets:
        relative_intensity = (weight / max_1rm) * 100
        if relative_intensity >= 85:
            zone = "Strength"
        elif 65 <= relative_intensity < 85:
            zone = "Hypertrophy"
        else:
            zone = "Endurance"

        results.append({
            "date": date.format(),
            "weight": weight,
            "reps": reps,
            "estimated_1rm": round(est_1rm, 1),
            "relative_intensity": round(relative_intensity, 1),
            "zone": zone
        })

    return jsonify(results)
