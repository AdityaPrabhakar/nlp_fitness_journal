from flask import Blueprint, request, render_template, redirect, jsonify, flash
from datetime import datetime, date
from models import WorkoutSession, WorkoutEntry, StrengthEntry, CardioEntry
from models.goal import Goal, GoalTarget
from utils.openai_utils import parse_workout, clean_entries, parse_goals
from init import db

log_entry_bp = Blueprint("log_entry", __name__)

def parse_iso_date(s):
    return datetime.strptime(s, "%Y-%m-%d").date()

@log_entry_bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        raw_text = request.form["entry"]
        today_date = datetime.now().strftime("%Y-%m-%d")

        try:
            structured_response = parse_workout(raw_text)
            print(structured_response)
            goal_response = parse_goals(raw_text)

            entries = structured_response.get("entries", [])
            notes = structured_response.get("notes", "")
            parsed_date = structured_response.get("date")
            goals = goal_response.get("goals", [])

            cleaned_entries = clean_entries(entries)

        except Exception as e:
            print("Error parsing:", e)
            cleaned_entries = []
            notes = ""
            goals = []
            parsed_date = None

        session = None

        if cleaned_entries:
            session = WorkoutSession(
                date=parsed_date or today_date,
                raw_text=raw_text,
                notes=notes
            )
            db.session.add(session)
            db.session.commit()

            for item in cleaned_entries:
                entry = WorkoutEntry.from_dict(item, session.id)
                db.session.add(entry)

            flash("Workout entry created successfully!")  # ✅ Success message

        for goal in goals:
            try:
                start_date = parse_iso_date(goal.get("start_date")) if goal.get("start_date") else date.today()
                end_date = parse_iso_date(goal.get("end_date")) if goal.get("end_date") else None

                new_goal = Goal(
                    exercise=goal["exercise"],
                    start_date=start_date,
                    end_date=end_date,
                    status="active"
                )
                db.session.add(new_goal)
                db.session.flush()

                for target in goal.get("targets", []):
                    target_field = target.get("target_field")
                    target_value = target.get("target_value")
                    if target_field and target_value is not None:
                        goal_target = GoalTarget(
                            goal_id=new_goal.id,
                            target_field=target_field,
                            target_value=target_value
                        )
                        db.session.add(goal_target)
            except Exception as e:
                print("Error processing goal:", e)

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


