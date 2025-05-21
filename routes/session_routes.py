from flask import Blueprint, jsonify, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import WorkoutSession, WorkoutEntry, StrengthEntry, CardioEntry
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


# Endpoint to fetch a specific session's details
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

    return jsonify({
        'id': session.id,
        'date': session.date,
        'raw_text': session.raw_text,
        'notes': session.notes,
        'entries': entry_list
    })
