from flask import Blueprint, request, render_template, jsonify
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import WorkoutSession, WorkoutEntry, StrengthEntry, CardioEntry, PersonalRecord
from utils import track_prs_for_session
from utils.openai_utils import parse_workout, clean_entries
from init import db

log_entry_bp = Blueprint("log_entry", __name__)

@log_entry_bp.route("/", methods=["GET"])
def index():
    return render_template("index.html")  # Just return the template

@log_entry_bp.route("/api/dashboard-data", methods=["GET"])
@jwt_required()
def dashboard_data():
    user_id = get_jwt_identity()

    cardio_exercises = (
        db.session.query(WorkoutEntry.exercise)
        .filter_by(type='cardio', user_id=user_id)
        .distinct()
        .all()
    )
    strength_exercises = (
        db.session.query(WorkoutEntry.exercise)
        .filter_by(type='strength', user_id=user_id)
        .distinct()
        .all()
    )
    sessions = (
        WorkoutSession.query
        .filter_by(user_id=user_id)
        .order_by(WorkoutSession.id.desc())
        .all()
    )

    return jsonify({
        "cardio_exercises": [e[0] for e in cardio_exercises],
        "strength_exercises": [e[0] for e in strength_exercises],
        "sessions": [s.to_dict() for s in sessions]  # ensure WorkoutSession has a `.to_dict()`
    })


@log_entry_bp.route("/log-entry")
def show_log_form():
    return render_template("partials/form.html")

@log_entry_bp.route("/api/log-workout", methods=["POST"])
@jwt_required()
def log_workout():
    user_id = get_jwt_identity()
    raw_text = request.form.get("entry") or request.json.get("entry")
    today_date = datetime.now().strftime("%Y-%m-%d")
    new_prs = []

    try:
        structured_response = parse_workout(raw_text)
        entries = structured_response.get("entries", [])
        notes = structured_response.get("notes", "")
        parsed_date = structured_response.get("date")
        cleaned_entries = clean_entries(entries)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

    session = None
    if cleaned_entries:
        session = WorkoutSession(
            user_id=user_id,
            date=parsed_date or today_date,
            raw_text=raw_text,
            notes=notes,
        )
        db.session.add(session)
        db.session.commit()

        for item in cleaned_entries:
            WorkoutEntry.from_dict(item, session.id)

        db.session.commit()

        new_prs = track_prs_for_session(session, cleaned_entries)

    return jsonify({
        "success": True,
        "message": "Workout entry created successfully!",
        "session_id": session.id if session else None,
        "session_date": session.date.format() if session else None,
        "new_prs": new_prs
    }), 201


@log_entry_bp.route("/api/edit-workout/<int:session_id>", methods=["POST"])
@jwt_required()
def edit_workout(session_id):
    user_id = get_jwt_identity()
    raw_text = request.form.get("raw_text") or request.json.get("raw_text")

    if not raw_text:
        return jsonify({"success": False, "error": "No entry provided."}), 400

    session = db.session.get(WorkoutSession, session_id)
    if not session or session.user_id != user_id:
        return jsonify({"success": False, "error": "Workout session not found or access denied."}), 404

    try:
        structured_response = parse_workout(raw_text)
        entries = structured_response.get("entries", [])
        notes = structured_response.get("notes", "")
        parsed_date = structured_response.get("date")
        cleaned_entries = clean_entries(entries)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

    try:
        # Delete existing entries and their children
        entry_ids = [e.id for e in WorkoutEntry.query.filter_by(session_id=session.id, user_id=user_id).all()]
        StrengthEntry.query.filter(StrengthEntry.entry_id.in_(entry_ids)).delete(synchronize_session=False)
        CardioEntry.query.filter(CardioEntry.entry_id.in_(entry_ids)).delete(synchronize_session=False)
        WorkoutEntry.query.filter(WorkoutEntry.id.in_(entry_ids)).delete(synchronize_session=False)

        # Add new entries
        for item in cleaned_entries:
            WorkoutEntry.from_dict(item, session.id)

        # Update session metadata
        session.raw_text = raw_text
        session.notes = notes
        if parsed_date:
            session.date = parsed_date

        db.session.flush()
        new_prs = track_prs_for_session(session, cleaned_entries)

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Workout session updated successfully!",
            "session_id": session.id,
            "new_prs": new_prs
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@log_entry_bp.route("/api/logs/strength/<exercise>")
@jwt_required()
def get_strength_logs(exercise):
    user_id = get_jwt_identity()
    logs = (
        db.session.query(
            StrengthEntry.set_number,
            StrengthEntry.reps,
            StrengthEntry.weight,
            WorkoutSession.date,
            WorkoutEntry.notes.label('workout_entry_notes')
        )
        .join(WorkoutSession, WorkoutSession.id == WorkoutEntry.session_id)
        .outerjoin(StrengthEntry, StrengthEntry.entry_id == WorkoutEntry.id)
        .filter(
            WorkoutEntry.exercise == exercise,
            WorkoutEntry.type == 'strength',
            WorkoutEntry.user_id == user_id
        )
        .order_by(WorkoutSession.date.desc())
        .all()
    )

    return jsonify([
        {
            "date": log.date,
            "sets": log.set_number,
            "reps": log.reps,
            "weight": log.weight,
            "notes": log.workout_entry_notes
        } for log in logs
    ])

@log_entry_bp.route("/api/logs/cardio/<exercise>")
@jwt_required()
def get_cardio_logs(exercise):
    user_id = get_jwt_identity()
    logs = (
        db.session.query(
            CardioEntry.duration,
            CardioEntry.distance,
            WorkoutSession.date,
            WorkoutEntry.notes
        )
        .join(WorkoutSession)
        .join(CardioEntry)
        .filter(
            WorkoutEntry.exercise == exercise,
            WorkoutEntry.type == 'cardio',
            WorkoutEntry.user_id == user_id
        )
        .order_by(WorkoutSession.date.desc())
        .all()
    )

    return jsonify([
        {
            "date": log.date,
            "duration": log.duration,
            "distance": log.distance,
            "notes": log.notes
        } for log in logs
    ])

@log_entry_bp.route("/api/logs/by-date")
@jwt_required()
def get_logs_by_date():
    user_id = get_jwt_identity()
    sessions = (
        db.session.query(WorkoutSession)
        .filter_by(user_id=user_id)
        .order_by(WorkoutSession.date.desc())
        .all()
    )

    data = []
    for session in sessions:
        entries = WorkoutEntry.query.filter_by(session_id=session.id, user_id=user_id).all()
        entry_data = []

        for e in entries:
            if e.type == 'cardio':
                cardio_data = (
                    db.session.query(CardioEntry)
                    .filter_by(entry_id=e.id)
                    .first()
                )
                entry_data.append({
                    "exercise": e.exercise,
                    "type": e.type,
                    "duration": cardio_data.duration if cardio_data else None,
                    "distance": cardio_data.distance if cardio_data else None,
                    "notes": cardio_data.notes if cardio_data else None
                })
            else:
                strength_data = (
                    db.session.query(StrengthEntry)
                    .filter_by(entry_id=e.id)
                    .all()
                )
                strength_entries = [
                    {
                        "set_number": entry.set_number,
                        "reps": entry.reps,
                        "weight": entry.weight,
                        "notes": entry.notes
                    } for entry in strength_data
                ]
                entry_data.append({
                    "exercise": e.exercise,
                    "type": e.type,
                    "sets": strength_entries
                })

        data.append({
            "date": session.date,
            "entries": entry_data
        })

    return jsonify(data)
