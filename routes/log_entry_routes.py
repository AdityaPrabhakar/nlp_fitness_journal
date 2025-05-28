from flask import Blueprint, request, render_template, jsonify
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import and_

from models import WorkoutSession, WorkoutEntry, StrengthEntry, CardioEntry, PersonalRecord, User
from models.goal import Goal, GoalTypeEnum, RepeatIntervalEnum, ExerciseTypeEnum, MetricEnum, GoalTarget
from utils import track_prs_for_session
from utils.openai_utils import clean_entries, parse_workout_and_goals
from init import db

log_entry_bp = Blueprint("log_entry", __name__)

@log_entry_bp.route("/", methods=["GET"])
def index():
    return render_template("index.html")  # Just return the template

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
        structured_response = parse_workout_and_goals(raw_text)
        entries = structured_response.get("entries", [])
        goals = structured_response.get("goals", [])
        notes = structured_response.get("notes", "")
        parsed_date = structured_response.get("date")
        cleaned_entries = clean_entries(entries)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

    session = None
    goals_added = 0

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

    for goal in goals:
        try:
            # Parse base fields
            start_date = datetime.strptime(goal["start_date"], "%Y-%m-%d").date()
            end_date = datetime.strptime(goal["end_date"], "%Y-%m-%d").date() if goal.get("end_date") else None
            goal_type = GoalTypeEnum(goal["goal_type"])
            is_repeatable = goal.get("is_repeatable", False)
            repeat_interval = RepeatIntervalEnum(goal["repeat_interval"]) if goal.get("repeat_interval") else None
            exercise_type = ExerciseTypeEnum(goal["exercise_type"]) if goal.get("exercise_type") else None
            exercise_name = goal.get("exercise_name")
            targets = goal.get("targets", {})

            if not isinstance(targets, list) or not targets:
                raise ValueError("Goal must include at least one target metric.")

            for target in targets:
                if not isinstance(target, dict) or "target_metric" not in target or "target_value" not in target:
                    raise ValueError("Each target must include 'target_metric' and 'target_value'.")

            # Check for duplicate by base fields
            existing_goals = Goal.query.filter(
                and_(
                    Goal.user_id == user_id,
                    Goal.start_date == start_date,
                    Goal.end_date == end_date,
                    Goal.goal_type == goal_type,
                    Goal.is_repeatable == is_repeatable,
                    Goal.repeat_interval == repeat_interval,
                    Goal.exercise_type == exercise_type,
                    Goal.exercise_name == exercise_name,
                )
            ).all()

            is_duplicate = False
            for g in existing_goals:
                existing_targets = {(t.metric.value, t.value) for t in g.targets}
                incoming_targets = {(k, float(v)) for k, v in targets.items()}
                if existing_targets == incoming_targets:
                    is_duplicate = True
                    break

            if is_duplicate:
                continue  # Skip duplicate

            # Create goal
            goal_obj = Goal(
                user_id=user_id,
                name=goal.get("name", f"{goal_type.value.capitalize()} goal for {exercise_name or 'general'}"),
                description=goal.get("description", ""),
                start_date=start_date,
                end_date=end_date,
                goal_type=goal_type,
                is_repeatable=is_repeatable,
                repeat_interval=repeat_interval,
                exercise_type=exercise_type,
                exercise_name=exercise_name,
                created_at=datetime.utcnow(),
            )

            for target in targets:
                metric_str = target["target_metric"]
                value = target["target_value"]
                metric_enum = MetricEnum(metric_str)
                goal_obj.targets.append(GoalTarget(metric=metric_enum, value=float(value)))

            db.session.add(goal_obj)
            goals_added += 1

        except Exception as e:
            print(f"Error processing goal: {goal} — {e}")

    if goals_added:
        db.session.commit()

    return jsonify({
        "success": True,
        "message": "Workout entry created successfully!",
        "session_id": session.id if session else None,
        "session_date": session.date.format() if session else None,
        "new_prs": new_prs,
        "goals_added": goals_added
    }), 201


@log_entry_bp.route("/api/edit-workout/<int:session_id>", methods=["POST"])
@jwt_required()
def edit_workout(session_id):
    user_id = int(get_jwt_identity())
    raw_text = request.form.get("raw_text") or request.json.get("raw_text")

    if not raw_text:
        return jsonify({"success": False, "error": "No entry provided."}), 400

    session = db.session.get(WorkoutSession, session_id)

    if not session or session.user_id != user_id:
        return jsonify({"success": False, "error": "Workout session not found or access denied."}), 404

    try:
        structured_response = parse_workout_and_goals(raw_text)
        entries = structured_response.get("entries", [])
        notes = structured_response.get("notes", "")
        parsed_date = structured_response.get("date")
        cleaned_entries = clean_entries(entries)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

    try:
        # Delete existing entries and their children
        entry_ids = [e.id for e in WorkoutEntry.query.filter_by(session_id=session.id).all()]
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

