from datetime import datetime

from flask import Blueprint, jsonify, render_template, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.orm import joinedload

from models import WorkoutSession, WorkoutEntry, StrengthEntry, CardioEntry, Goal
from init import db

session_bp = Blueprint('session', __name__)


@session_bp.route("/view-entries")
def view_entries():
    return render_template("partials/sessions.html")


# Endpoint to fetch all workout sessions for the user
@session_bp.route('/api/sessions', methods=['GET'])
@jwt_required()
def get_all_sessions():
    user_id = get_jwt_identity()
    sessions = WorkoutSession.query.filter_by(user_id=user_id).all()

    result = []
    for session in sessions:
        result.append({
            'id': session.id,
            'date': session.date,
            'raw_text': session.raw_text
        })
    return jsonify(result)


@session_bp.route('/api/session/<int:session_id>', methods=['GET'])
@jwt_required()
def get_session_details(session_id):
    user_id = get_jwt_identity()
    session = WorkoutSession.query.filter_by(id=session_id, user_id=user_id).first()
    if not session:
        return jsonify({'error': 'Session not found'}), 404

    entries = WorkoutEntry.query.filter_by(session_id=session.id).all()
    entry_list = []

    for entry in entries:
        entry_data = {
            'exercise': entry.exercise,
            'type': entry.type,
            'notes': entry.notes
        }

        if entry.type == "strength":
            sets = StrengthEntry.query.filter_by(entry_id=entry.id).order_by(StrengthEntry.set_number).all()
            entry_data["sets_details"] = [
                {
                    "set_number": s.set_number,
                    "reps": s.reps,
                    "weight": s.weight
                } for s in sets
            ]
        elif entry.type == "cardio":
            cardio = CardioEntry.query.filter_by(entry_id=entry.id).first()
            if cardio:
                entry_data["duration"] = cardio.duration
                entry_data["distance"] = cardio.distance

        entry_list.append(entry_data)

    # Fetch and serialize goals associated with the session
    goals = Goal.query.filter_by(session_id=session.id).all()
    goals_data = []
    for g in goals:
        goals_data.append({
            "id": g.id,
            "name": g.name,
            "description": g.description,
            "start_date": g.start_date.isoformat(),
            "end_date": g.end_date.isoformat() if g.end_date else None,
            "goal_type": g.goal_type.value,
            "exercise_type": g.exercise_type.value if g.exercise_type else None,
            "exercise_name": g.exercise_name,
            "is_complete": g.is_complete,
            "is_expired": g.is_expired,
            "targets": [
                {
                    "target_metric": t.metric.value,
                    "target_value": t.value
                } for t in g.targets
            ]
        })

    return jsonify({
        'id': session.id,
        'date': session.date,
        'raw_text': session.raw_text,
        'notes': session.notes,
        'entries': entry_list,
        'goals': goals_data
    })


@session_bp.route("/api/sessions/by-exercise", methods=["GET"])
@jwt_required()
def get_sessions_by_exercise():
    user_id = get_jwt_identity()

    exercise = request.args.get("exercise")
    if not exercise:
        return jsonify({"error": "Missing exercise parameter"}), 400

    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    # Base query for user's sessions
    query = db.session.query(WorkoutSession).filter(
        WorkoutSession.user_id == user_id
    ).options(
        joinedload(WorkoutSession.entries)
        .joinedload(WorkoutEntry.strength_entries),
        joinedload(WorkoutSession.entries)
        .joinedload(WorkoutEntry.cardio_detail)
    )

    # Filter by date range
    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            query = query.filter(WorkoutSession.date >= start_date)
        except ValueError:
            return jsonify({"error": "Invalid start_date format"}), 400

    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
            query = query.filter(WorkoutSession.date <= end_date)
        except ValueError:
            return jsonify({"error": "Invalid end_date format"}), 400

    sessions = query.order_by(WorkoutSession.date).all()

    output = []
    for session in sessions:
        session_data = {
            "id": session.id,
            "date": session.date,
            "entries": []
        }

        for entry in session.entries:
            if entry.exercise != exercise:
                continue

            entry_data = {
                "exercise": entry.exercise,
                "type": entry.type,
                "notes": entry.notes,
            }

            if entry.type == "strength" and entry.strength_entries:
                entry_data["sets"] = [
                    {
                        "set_number": s.set_number,
                        "reps": s.reps,
                        "weight": s.weight
                    }
                    for s in sorted(entry.strength_entries, key=lambda s: s.set_number)
                ]
            elif entry.type == "cardio" and entry.cardio_detail:
                entry_data.update({
                    "distance": entry.cardio_detail.distance,
                    "duration": entry.cardio_detail.duration,
                    "pace" : entry.cardio_detail.pace
                })

            session_data["entries"].append(entry_data)

        if session_data["entries"]:
            output.append(session_data)

    return jsonify(output)