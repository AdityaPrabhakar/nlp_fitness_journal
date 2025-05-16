from flask import Blueprint, request, render_template, redirect, jsonify, flash
from datetime import datetime, date
from models import WorkoutSession, WorkoutEntry, StrengthEntry, CardioEntry, PersonalRecord
from utils import track_prs_for_session
from utils.openai_utils import parse_workout, clean_entries
from init import db

log_entry_bp = Blueprint("log_entry", __name__)

def parse_iso_date(s):
    return datetime.strptime(s, "%Y-%m-%d").date()

@log_entry_bp.route("/", methods=["GET"])
def index():
    cardio_exercises = db.session.query(WorkoutEntry.exercise).filter_by(type='cardio').distinct().all()
    strength_exercises = db.session.query(WorkoutEntry.exercise).filter_by(type='strength').distinct().all()

    sessions = WorkoutSession.query.order_by(WorkoutSession.id.desc()).all()
    return render_template("index.html",
        sessions=sessions,
        cardio_exercises=[e[0] for e in cardio_exercises],
        strength_exercises=[e[0] for e in strength_exercises]
    )


@log_entry_bp.route("/api/log-workout", methods=["POST"])
def log_workout():
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
            date=parsed_date or today_date,
            raw_text=raw_text,
            notes=notes,
        )
        db.session.add(session)
        db.session.commit()

        for item in cleaned_entries:
            entry = WorkoutEntry.from_dict(item, session.id)
            db.session.add(entry)
        db.session.commit()

        # 🧠 PR Tracking moved to helper
        new_prs = track_prs_for_session(session, cleaned_entries)

    return jsonify({
        "success": True,
        "message": "Workout entry created successfully!",
        "session_id": session.id if session else None,
        "new_prs": new_prs
    }), 201



@log_entry_bp.route("/api/edit-workout/<int:session_id>", methods=["POST"])
def edit_workout(session_id):
    print(f"[INFO] Received request to edit session {session_id}")

    raw_text = request.form.get("raw_text") or request.json.get("raw_text")
    print(f"[DEBUG] Raw text received:\n{raw_text}")

    if not raw_text:
        print("[ERROR] No entry provided in the request")
        return jsonify({"success": False, "error": "No entry provided."}), 400

    session = db.session.get(WorkoutSession, session_id)
    if not session:
        print(f"[ERROR] Workout session with ID {session_id} not found")
        return jsonify({"success": False, "error": "Workout session not found."}), 404

    try:
        structured_response = parse_workout(raw_text)
        print(f"[DEBUG] Structured response: {structured_response}")

        entries = structured_response.get("entries", [])
        notes = structured_response.get("notes", "")
        parsed_date = structured_response.get("date")
        cleaned_entries = clean_entries(entries)
        print(f"[INFO] Parsed {len(cleaned_entries)} cleaned entries")

    except Exception as e:
        print(f"[ERROR] Exception while parsing workout text: {e}")
        return jsonify({"success": False, "error": str(e)}), 400

    try:
        # Get all WorkoutEntry IDs for the session
        entry_ids = [e.id for e in WorkoutEntry.query.filter_by(session_id=session.id).all()]
        print(f"[INFO] Found {len(entry_ids)} workout entries to delete associated strength/cardio data")

        # Delete associated StrengthEntry and CardioEntry records
        strength_deleted = StrengthEntry.query.filter(StrengthEntry.entry_id.in_(entry_ids)).delete(synchronize_session=False)
        cardio_deleted = CardioEntry.query.filter(CardioEntry.entry_id.in_(entry_ids)).delete(synchronize_session=False)
        print(f"[INFO] Deleted {strength_deleted} strength entries and {cardio_deleted} cardio entries")

        # Delete the WorkoutEntry records themselves
        workout_deleted = WorkoutEntry.query.filter(WorkoutEntry.id.in_(entry_ids)).delete(synchronize_session=False)
        print(f"[INFO] Deleted {workout_deleted} workout entries")

        # Re-create updated WorkoutEntries
        for idx, item in enumerate(cleaned_entries):
            print(f"[INFO] Creating entry {idx + 1}: {item}")
            entry = WorkoutEntry.from_dict(item, session.id)
            db.session.add(entry)

        # Update session metadata
        session.raw_text = raw_text
        session.notes = notes
        if parsed_date:
            session.date = parsed_date

        db.session.flush()  # Ensure new entries are staged in the session

        # 🏅 Track personal records
        new_prs = track_prs_for_session(session, cleaned_entries)
        print(f"[INFO] New PRs: {new_prs}")

        db.session.commit()
        print(f"[SUCCESS] Workout session {session.id} updated successfully")

        return jsonify({
            "success": True,
            "message": "Workout session updated successfully!",
            "session_id": session.id,
            "new_prs": new_prs
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] Exception while updating workout session: {e}")
        return jsonify({"success": False, "error": str(e)}), 500



@log_entry_bp.route("/api/logs/strength/<exercise>")
def get_strength_logs(exercise):
    # Perform a LEFT JOIN to include entries even without associated StrengthEntry
    logs = (
        db.session.query(
            StrengthEntry.set_number,
            StrengthEntry.reps,
            StrengthEntry.weight,
            WorkoutSession.date,
            WorkoutEntry.notes.label('workout_entry_notes')  # Alias to avoid ambiguity
        )
        .join(WorkoutSession, WorkoutSession.id == WorkoutEntry.session_id)  # Join WorkoutSession
        .outerjoin(StrengthEntry, StrengthEntry.entry_id == WorkoutEntry.id)  # LEFT OUTER JOIN StrengthEntry
        .filter(
            WorkoutEntry.exercise == exercise,  # Filter by the exercise field in WorkoutEntry
            WorkoutEntry.type == 'strength'  # Only strength entries
        )
        .order_by(WorkoutSession.date.desc())
        .all()
    )

    return jsonify([
        {
            "date": log.date,
            "sets": log.set_number if log.set_number is not None else None,  # Return None if no set_number
            "reps": log.reps if log.reps is not None else None,  # Return None if no reps
            "weight": log.weight if log.weight is not None else None,  # Return None if no weight
            "notes": log.workout_entry_notes or None  # Return None if no notes
        } for log in logs
    ])






@log_entry_bp.route("/api/logs/cardio/<exercise>")
def get_cardio_logs(exercise):
    logs = (
        db.session.query(
            CardioEntry.duration,
            CardioEntry.distance,
            WorkoutSession.date,
            WorkoutEntry.notes
        )
        .join(WorkoutSession)
        .join(CardioEntry)  # Join CardioEntry to access cardio details
        .filter(
            WorkoutEntry.exercise == exercise,  # Filter by the exercise field in WorkoutEntry
            WorkoutEntry.type == 'cardio'  # Make sure we're querying for cardio entries
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
def get_logs_by_date():
    # Query for all workout sessions
    sessions = (
        db.session.query(WorkoutSession)
        .order_by(WorkoutSession.date.desc())
        .all()
    )

    data = []
    for session in sessions:
        # Get all workout entries for the session
        entries = WorkoutEntry.query.filter_by(session_id=session.id).all()
        entry_data = []

        for e in entries:
            if e.type == 'cardio':
                # For cardio, fetch data from CardioEntry
                cardio_data = (
                    db.session.query(CardioEntry)
                    .filter(CardioEntry.session_id == session.id)
                    .filter(CardioEntry.exercise == e.exercise)
                    .first()
                )
                entry_data.append({
                    "exercise": cardio_data.exercise,
                    "type": e.type,
                    "duration": cardio_data.duration,
                    "distance": cardio_data.distance,
                    "notes": cardio_data.notes,
                })
            else:
                # For strength, fetch data from StrengthEntry
                strength_data = (
                    db.session.query(StrengthEntry)
                    .filter(StrengthEntry.session_id == session.id)
                    .filter(StrengthEntry.exercise == e.exercise)
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

        # Add entry data to session data
        data.append({
            "date": session.date,
            "entries": entry_data
        })

    return jsonify(data)


