from flask import Blueprint, request, render_template, redirect
from datetime import datetime
from models import WorkoutSession
from models import WorkoutEntry
from utils.openai_utils import parse_workout
from init import db

log_entry_bp = Blueprint("log_entry", __name__)

@log_entry_bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        raw_text = request.form["entry"]
        now = datetime.now().strftime("%Y-%m-%d")

        try:
            structured_response = parse_workout(raw_text)
            parsed = structured_response.get("entries", [])
        except Exception as e:
            print("Error parsing:", e)
            parsed = []

        session = WorkoutSession(date=now, raw_text=raw_text)
        db.session.add(session)
        db.session.commit()

        for item in parsed:
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
