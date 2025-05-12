from flask import Blueprint, request, render_template, redirect, jsonify
from datetime import datetime
from models import WorkoutSession
from models import WorkoutEntry
from utils.openai_utils import parse_workout, clean_entries
from init import db

log_entry_bp = Blueprint("log_entry", __name__)

@log_entry_bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        raw_text = request.form["entry"]
        now_date = datetime.now().strftime("%Y-%m-%d")

        try:
            structured_response = parse_workout(raw_text)

            entries = structured_response.get("entries", [])
            notes = structured_response.get("notes", "")

            cleaned_entries = clean_entries(entries)

        except Exception as e:
            print("Error parsing:", e)
            cleaned_entries = []
            notes = ""

        # Always create a new WorkoutSession even if one exists on the same date
        session = WorkoutSession(
            date=now_date,
            raw_text=raw_text,
            notes=notes
        )
        db.session.add(session)
        db.session.commit()  # Get session.id

        for item in cleaned_entries:
            entry = WorkoutEntry.from_dict(item, session.id)
            db.session.add(entry)

        db.session.commit()
        return redirect("/")

    cardio_exercises = db.session.query(WorkoutEntry.exercise).filter_by(type='cardio').distinct().all()
    strength_exercises = db.session.query(WorkoutEntry.exercise).filter_by(type='strength').distinct().all()

    sessions = WorkoutSession.query.order_by(WorkoutSession.id.desc()).all()
    return render_template("index.html",
        sessions=sessions,
        cardio_exercises=[e[0] for e in cardio_exercises],
        strength_exercises=[e[0] for e in strength_exercises]
    )



@log_entry_bp.route("/api/logs/strength/<exercise>")
def get_strength_logs(exercise):
    logs = (
        db.session.query(
            WorkoutEntry.sets,
            WorkoutEntry.reps,
            WorkoutEntry.weight,
            WorkoutSession.date,
            WorkoutEntry.notes
        )
        .join(WorkoutSession)
        .filter(WorkoutEntry.exercise == exercise)
        .order_by(WorkoutSession.date.desc())
        .all()
    )

    return jsonify([
        {
            "date": log.date,
            "sets": log.sets,
            "reps": log.reps,
            "weight": log.weight,
            "notes": log.notes
        }
        for log in logs
    ])

@log_entry_bp.route("/api/logs/cardio/<exercise>")
def get_cardio_logs(exercise):
    logs = (
        db.session.query(
            WorkoutSession.date,
            WorkoutEntry.duration,
            WorkoutEntry.distance,
            WorkoutEntry.notes
        )
        .join(WorkoutSession)
        .filter(
            WorkoutEntry.type == 'cardio',
            WorkoutEntry.exercise == exercise
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
    sessions = (
        db.session.query(WorkoutSession)
        .order_by(WorkoutSession.date.desc())
        .all()
    )

    data = []
    for session in sessions:
        entries = WorkoutEntry.query.filter_by(session_id=session.id).all()
        entry_data = [
            {
                "exercise": e.exercise,
                "type": e.type,
                "sets": e.sets,
                "reps": e.reps,
                "weight": e.weight,
                "duration": e.duration,
                "distance": e.distance,
                "notes": e.notes,
            }
            for e in entries
        ]
        data.append({
            "date": session.date,
            "entries": entry_data
        })

    return jsonify(data)
