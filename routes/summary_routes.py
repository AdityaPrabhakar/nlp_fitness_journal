from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from models import WorkoutSession, WorkoutEntry, StrengthEntry, CardioEntry, PersonalRecord
from init import db

summary_bp = Blueprint("summary", __name__)

@summary_bp.route("/api/summary/overview", methods=["GET"])
@jwt_required()
def summary_overview():
    user_id = get_jwt_identity()
    days = request.args.get("days", default=7, type=int)
    start_date = datetime.now().date() - timedelta(days=days)

    total_sessions = db.session.query(WorkoutSession).filter(
        WorkoutSession.user_id == user_id,
        WorkoutSession.date >= start_date
    ).count()

    strength_session_ids = db.session.query(WorkoutEntry.session_id).filter_by(
        type="strength"
    ).join(WorkoutSession, WorkoutEntry.session_id == WorkoutSession.id
    ).filter(WorkoutSession.user_id == user_id).distinct().all()
    strength_session_ids = {sid for (sid,) in strength_session_ids}

    cardio_session_ids = db.session.query(WorkoutEntry.session_id).filter_by(
        type="cardio"
    ).join(WorkoutSession, WorkoutEntry.session_id == WorkoutSession.id
    ).filter(WorkoutSession.user_id == user_id).distinct().all()
    cardio_session_ids = {sid for (sid,) in cardio_session_ids}

    recent_session_ids = db.session.query(WorkoutSession.id).filter(
        WorkoutSession.user_id == user_id,
        WorkoutSession.date >= start_date
    ).all()
    recent_session_ids = {sid for (sid,) in recent_session_ids}

    strength_sessions = len(recent_session_ids & strength_session_ids)
    cardio_sessions = len(recent_session_ids & cardio_session_ids)

    return jsonify({
        "success": True,
        "total_sessions": total_sessions,
        "strength_sessions": strength_sessions,
        "cardio_sessions": cardio_sessions
    })

@summary_bp.route("/api/summary/cardio", methods=["GET"])
@jwt_required()
def cardio_summary():
    user_id = get_jwt_identity()
    try:
        days = int(request.args.get("days", 7))
        if days < 1 or days > 90:
            return jsonify({"success": False, "error": "Days must be between 1 and 90"}), 400
    except ValueError:
        return jsonify({"success": False, "error": "Invalid days parameter"}), 400

    today = datetime.now().date()
    start_date = today - timedelta(days=days - 1)
    date_labels = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
    summary_map = {date: {"total_distance": 0.0, "total_duration": 0.0} for date in date_labels}

    results = (
        db.session.query(
            WorkoutSession.date,
            func.sum(CardioEntry.distance).label("total_distance"),
            func.sum(CardioEntry.duration).label("total_duration")
        )
        .join(WorkoutEntry, WorkoutEntry.session_id == WorkoutSession.id)
        .join(CardioEntry, CardioEntry.entry_id == WorkoutEntry.id)
        .filter(
            WorkoutSession.user_id == user_id,
            WorkoutSession.date >= start_date
        )
        .group_by(WorkoutSession.date)
        .all()
    )

    for row in results:
        date_str = str(row.date)
        if date_str in summary_map:
            summary_map[date_str]["total_distance"] = float(row.total_distance or 0)
            summary_map[date_str]["total_duration"] = float(row.total_duration or 0)

    return jsonify({
        "success": True,
        "days": days,
        "daily_cardio": [
            {"date": date, **summary_map[date]} for date in date_labels
        ]
    })

@summary_bp.route("/api/summary/strength", methods=["GET"])
@jwt_required()
def strength_summary():
    user_id = get_jwt_identity()
    try:
        days = int(request.args.get("days", 7))
        if days < 1 or days > 90:
            return jsonify({"success": False, "error": "Days must be between 1 and 90"}), 400
    except ValueError:
        return jsonify({"success": False, "error": "Invalid days parameter"}), 400

    today = datetime.now().date()
    start_date = today - timedelta(days=days - 1)

    print(f"User ID: {user_id}")
    print(f"Start date: {start_date}")
    print(
        f"Workout sessions in range: {db.session.query(WorkoutSession).filter(WorkoutSession.user_id == user_id, WorkoutSession.date >= start_date).count()}")
    print(
        f"Workout entries: {db.session.query(WorkoutEntry).join(WorkoutSession).filter(WorkoutSession.user_id == user_id).count()}")
    print(
        f"Strength entries: {db.session.query(StrengthEntry).join(WorkoutEntry).join(WorkoutSession).filter(WorkoutSession.user_id == user_id, WorkoutSession.date >= start_date).count()}")

    results = (
        db.session.query(
            WorkoutEntry.exercise,
            func.count(StrengthEntry.id).label("total_sets")
        )
        .join(WorkoutSession, WorkoutSession.id == WorkoutEntry.session_id)
        .join(StrengthEntry, StrengthEntry.entry_id == WorkoutEntry.id)
        .filter(
            WorkoutSession.user_id == user_id,
            WorkoutSession.date >= start_date
        )
        .group_by(WorkoutEntry.exercise)
        .all()
    )

    summary = [
        {"exercise": row.exercise, "total_sets": int(row.total_sets or 0)}
        for row in results
    ]

    print(summary)

    return jsonify({
        "success": True,
        "days": days,
        "strength_summary": summary
    })

@summary_bp.route("/api/summary/prs")
@jwt_required()
def pr_summary():
    user_id = get_jwt_identity()
    days = request.args.get("days", default=7, type=int)
    start_date = datetime.now().date() - timedelta(days=days)

    prs = (
        db.session.query(
            PersonalRecord.exercise,
            PersonalRecord.type,
            PersonalRecord.field,
            PersonalRecord.value,
            PersonalRecord.session_id,
            WorkoutSession.date
        )
        .join(WorkoutSession, WorkoutSession.id == PersonalRecord.session_id)
        .filter(
            WorkoutSession.user_id == user_id,
            WorkoutSession.date >= start_date
        )
        .order_by(WorkoutSession.date.desc())
        .all()
    )

    result = [
        {
            "exercise": pr.exercise,
            "type": pr.type,
            "field": pr.field,
            "value": pr.value,
            "session_id": pr.session_id,
            "date": pr.date.format()
        }
        for pr in prs
    ]

    return jsonify({"prs": result})
