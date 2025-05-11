from flask import Blueprint, jsonify
from models import WorkoutSession, WorkoutEntry

session_bp = Blueprint('session', __name__)

# Endpoint to fetch all workout sessions
@session_bp.route('/api/sessions', methods=['GET'])
def get_all_sessions():
    sessions = WorkoutSession.query.all()
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
def get_session_details(session_id):
    session = WorkoutSession.query.get(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404

    entries = WorkoutEntry.query.filter_by(session_id=session.id).all()
    entry_list = []
    for entry in entries:
        entry_list.append({
            'exercise': entry.exercise,
            'type': entry.type,
            'sets': entry.sets,
            'reps': entry.reps,
            'weight': entry.weight,
            'duration': entry.duration,
            'distance': entry.distance,
            'notes': entry.notes
        })

    return jsonify({
        'date': session.date,
        'raw_text': session.raw_text,
        'notes': session.notes,
        'entries': entry_list
    })