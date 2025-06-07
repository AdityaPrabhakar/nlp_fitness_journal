from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta

from init import db
from models import WorkoutSession, WorkoutEntry, User, StrengthEntry, CardioEntry
from utils import estimate_1rm, apply_date_filters
from utils.openai_utils import recommend_followup_set, recommend_followup_cardio

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
@exercise_bp.route("/api/exercise-data/strength/1rm-trend/<string:exercise>")
@jwt_required()
def strength_1rm_trend(exercise):
    user_id = get_jwt_identity()
    formula = request.args.get("formula", "epley")

    user = db.session.get(User, user_id)
    if not user or not user.bodyweight:
        return jsonify({"error": "User bodyweight not available"}), 400

    query = db.session.query(WorkoutSession).filter(
        WorkoutSession.user_id == user_id
    ).options(
        joinedload(WorkoutSession.entries)
        .joinedload(WorkoutEntry.strength_entries)
    )

    query, err_resp, status = apply_date_filters(query)
    if err_resp:
        return err_resp, status

    sessions = query.order_by(WorkoutSession.date).all()
    bodyweight = user.bodyweight
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
                "date": session.date.isoformat(),
                "estimated_1rm": round(max_1rm, 2)
            })

    return jsonify(trend)

@exercise_bp.route("/api/exercise-data/strength/volume-trend/<string:exercise>")
@jwt_required()
def strength_volume_trend(exercise):
    user_id = get_jwt_identity()

    user = db.session.get(User, user_id)
    if not user or not user.bodyweight:
        return jsonify({"error": "User bodyweight not available"}), 400

    query = db.session.query(WorkoutSession).filter(
        WorkoutSession.user_id == user_id
    ).options(
        joinedload(WorkoutSession.entries)
        .joinedload(WorkoutEntry.strength_entries)
    )

    query, err_resp, status = apply_date_filters(query)
    if err_resp:
        return err_resp, status

    sessions = query.order_by(WorkoutSession.date).all()
    bodyweight = user.bodyweight
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
                "date": session.date.isoformat(),
                "volume": round(total_volume, 2)
            })

    return jsonify(trend)

@exercise_bp.route("/api/exercise-data/strength/relative-intensity/<string:exercise_name>")
@jwt_required()
def get_relative_intensity(exercise_name):
    user_id = get_jwt_identity()
    formula = request.args.get("formula", "epley").lower()

    user = db.session.get(User, user_id)
    if not user or not user.bodyweight:
        return jsonify({"error": "User bodyweight not available"}), 400

    body_weight = user.bodyweight

    # Base query
    query = db.session.query(
        StrengthEntry.reps,
        StrengthEntry.weight,
        StrengthEntry.set_number,
        WorkoutSession.date
    ).join(WorkoutEntry, StrengthEntry.entry_id == WorkoutEntry.id
    ).join(WorkoutSession, WorkoutEntry.session_id == WorkoutSession.id
    ).filter(
        WorkoutEntry.type == "strength",
        WorkoutEntry.exercise.ilike(exercise_name),
        WorkoutSession.user_id == user_id
    )

    # Apply date filters
    query, err_resp, status = apply_date_filters(query)
    if err_resp:
        return err_resp, status

    sets = query.order_by(WorkoutSession.date, StrengthEntry.set_number).all()

    parsed_sets = []
    all_1rms = []

    # Step 1: Parse all sets and calculate per-set 1RMs
    for reps, weight, set_number, date in sets:
        reps = reps or DEFAULT_REPS
        weight = weight if weight and weight > 0 else body_weight
        est_1rm = estimate_1rm(reps, weight, formula=formula)
        if est_1rm:
            parsed_sets.append({
                "set_number": set_number,
                "reps": reps,
                "weight": weight,
                "date": date,
                "estimated_1rm": est_1rm
            })
            all_1rms.append(est_1rm)

    if not all_1rms:
        return jsonify([])

    # Step 2: Use the highest 1RM as the reference
    reference_1rm = max(all_1rms)

    # Step 3: Compute relative intensity and training zone
    results = []
    for s in parsed_sets:
        relative_intensity = (s["weight"] / reference_1rm) * 100
        if relative_intensity >= 85:
            zone = "Strength"
        elif 65 <= relative_intensity < 85:
            zone = "Hypertrophy"
        else:
            zone = "Endurance"

        results.append({
            "set_number": s["set_number"],
            "date": s["date"].isoformat(),
            "weight": s["weight"],
            "reps": s["reps"],
            "estimated_1rm": round(s["estimated_1rm"], 1),
            "relative_intensity": round(relative_intensity, 1),
            "zone": zone
        })

    return jsonify(results)

@exercise_bp.route("/api/exercise-data/strength/ai-insights/<string:exercise_name>")
@jwt_required()
def suggest_next_set(exercise_name):
    user_id = get_jwt_identity()
    goal = request.args.get("goal", "increase 1RM slightly")
    formula = request.args.get("formula", "epley").lower()

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 400

    query = db.session.query(
        StrengthEntry.reps,
        StrengthEntry.weight,
        StrengthEntry.set_number,
        WorkoutSession.date,
        WorkoutSession.id.label("session_id")
    ).join(WorkoutEntry, StrengthEntry.entry_id == WorkoutEntry.id
    ).join(WorkoutSession, WorkoutEntry.session_id == WorkoutSession.id
    ).filter(
        WorkoutEntry.type == "strength",
        WorkoutEntry.exercise.ilike(exercise_name),
        WorkoutSession.user_id == user_id
    )

    # Apply optional date range
    query, err_resp, status = apply_date_filters(query)
    if err_resp:
        return err_resp, status

    sets = query.order_by(WorkoutSession.date, StrengthEntry.set_number).all()

    if not sets:
        return jsonify({"error": "No training data found for this exercise"}), 404

    sets_details = []
    for reps, weight, set_number, date, session_id in sets:
        set_info = {
            "session_id": session_id,
            "set_number": set_number,
            "reps": reps or DEFAULT_REPS,
            "date": date.isoformat()
        }
        if weight and weight > 0:
            set_info["weight"] = weight  # only include weight if explicitly provided
        sets_details.append(set_info)

    recommendation = recommend_followup_set(
        exercise_name,
        sets_details,
        goal=goal,
    )

    return jsonify(recommendation)

@exercise_bp.route("/api/exercise-data/cardio/ai-insights/<string:exercise_name>")
@jwt_required()
def suggest_next_cardio_session(exercise_name):
    import json
    from collections import defaultdict
    user_id = get_jwt_identity()
    goal = request.args.get("goal", "improve endurance slightly")

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 400

    query = db.session.query(
        CardioEntry.duration,
        CardioEntry.distance,
        WorkoutSession.date,
        WorkoutSession.id.label("session_id")
    ).join(WorkoutEntry, CardioEntry.entry_id == WorkoutEntry.id
    ).join(WorkoutSession, WorkoutEntry.session_id == WorkoutSession.id
    ).filter(
        WorkoutEntry.type == "cardio",
        WorkoutEntry.exercise.ilike(exercise_name),
        WorkoutSession.user_id == user_id
    )

    # Apply optional date range
    query, err_resp, status = apply_date_filters(query)
    if err_resp:
        return err_resp, status

    sessions = query.order_by(WorkoutSession.date).all()

    if not sessions:
        return jsonify({"error": "No cardio data found for this exercise"}), 404

    # Prepare data for AI
    session_data = []
    for dur, dist, date, session_id in sessions:
        if dur and dist and dist > 0:
            pace = round(dur / dist, 2)
        else:
            pace = None
        session_data.append({
            "session_id": session_id,
            "duration": dur,
            "distance": dist,
            "pace": pace,
            "date": date.isoformat()
        })

    return jsonify(recommend_followup_cardio(exercise_name, session_data, goal=goal))
