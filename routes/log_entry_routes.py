from flask import Blueprint, request, render_template, jsonify
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import and_

from models import WorkoutSession, WorkoutEntry, StrengthEntry, CardioEntry, PersonalRecord, User
from models.goal import Goal, GoalTypeEnum, RepeatIntervalEnum, ExerciseTypeEnum, MetricEnum, GoalTarget
from utils import track_prs_for_session, evaluate_goal
from utils.openai_utils import clean_entries, parse_workout_and_goals
from init import db

log_entry_bp = Blueprint("log_entry", __name__)

@log_entry_bp.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@log_entry_bp.route("/log-entry")
def show_log_form():
    return render_template("partials/form.html")

def process_goals_for_session(goals, user_id, session, allow_same_session_duplicate=False):
    added_goals = []
    repeated_goals = []

    for goal in goals:
        try:
            start_date = datetime.strptime(goal["start_date"], "%Y-%m-%d").date()
            end_date = datetime.strptime(goal["end_date"], "%Y-%m-%d").date() if goal.get("end_date") else None
            goal_type = GoalTypeEnum(goal["goal_type"])
            exercise_type = ExerciseTypeEnum(goal["exercise_type"]) if goal.get("exercise_type") else None
            exercise_name = goal.get("exercise_name")
            targets = goal.get("targets", [])

            if not isinstance(targets, list) or not targets:
                raise ValueError("Goal must include at least one target metric.")

            for target in targets:
                if not isinstance(target, dict) or "target_metric" not in target or "target_value" not in target:
                    raise ValueError("Each target must include 'target_metric' and 'target_value'.")

            print(f"\nProcessing new goal:\n"
                  f"User ID: {user_id}\n"
                  f"Start Date: {start_date}, End Date: {end_date}\n"
                  f"Goal Type: {goal_type}, Exercise Type: {exercise_type}, Exercise Name: {exercise_name}\n"
                  f"Targets: {targets}")

            filters = [
                Goal.user_id == user_id,
                Goal.start_date == start_date,
                Goal.end_date == end_date,
                Goal.goal_type == goal_type,
                Goal.exercise_type == exercise_type,
                Goal.exercise_name == exercise_name,
            ]
            if not allow_same_session_duplicate:
                filters.append(Goal.session_id != session.id)

            print("Querying existing goals with the following filter fields:")
            print(f"  user_id == {user_id}")
            print(f"  start_date == {start_date}")
            print(f"  end_date == {end_date}")
            print(f"  goal_type == {goal_type}")
            print(f"  exercise_type == {exercise_type}")
            print(f"  exercise_name == {exercise_name}")
            if not allow_same_session_duplicate:
                print(f"  session_id != {session.id}")

            existing_goals = Goal.query.filter(and_(*filters)).all()
            incoming_targets = {(t["target_metric"], float(t["target_value"])) for t in targets}
            print(f"Incoming target set: {incoming_targets}")

            for g in existing_goals:
                existing_target_set = {(t.metric.value, t.value) for t in g.targets}
                print(f"Existing goal ID {g.id} comparison:")
                print(f"  Targets: {existing_target_set}")
                print(f"  Match: {existing_target_set == incoming_targets}")

            duplicate_goal = next(
                (g for g in existing_goals if {(t.metric.value, t.value) for t in g.targets} == incoming_targets),
                None
            )

            if duplicate_goal:
                print(f"⚠️ Duplicate goal found: ID {duplicate_goal.id} — skipping creation.")
                repeated_goals.append({
                    "id": duplicate_goal.id,
                    "name": duplicate_goal.name,
                    "description": duplicate_goal.description,
                    "start_date": duplicate_goal.start_date.isoformat(),
                    "end_date": duplicate_goal.end_date.isoformat() if duplicate_goal.end_date else None,
                    "goal_type": duplicate_goal.goal_type.value,
                    "exercise_type": duplicate_goal.exercise_type.value if duplicate_goal.exercise_type else None,
                    "exercise_name": duplicate_goal.exercise_name,
                    "targets": [
                        {"target_metric": t.metric.value, "target_value": t.value}
                        for t in duplicate_goal.targets
                    ]
                })
                continue

            print(f"✅ No duplicate found — creating goal for '{exercise_name or 'general'}'.")

            goal_obj = Goal(
                user_id=user_id,
                session_id=session.id,
                name=goal.get("name", f"{goal_type.value.capitalize()} goal for {exercise_name or 'general'}"),
                description=goal.get("description", ""),
                start_date=start_date,
                end_date=end_date,
                goal_type=goal_type,
                exercise_type=exercise_type,
                exercise_name=exercise_name,
                created_at=datetime.utcnow(),
            )

            for target in targets:
                metric_enum = MetricEnum(target["target_metric"])
                goal_obj.targets.append(GoalTarget(metric=metric_enum, value=float(target["target_value"])))

            db.session.add(goal_obj)
            db.session.flush()

            added_goals.append({
                "id": goal_obj.id,
                "name": goal_obj.name,
                "description": goal_obj.description,
                "start_date": goal_obj.start_date.isoformat(),
                "end_date": goal_obj.end_date.isoformat() if goal_obj.end_date else None,
                "goal_type": goal_obj.goal_type.value,
                "exercise_type": goal_obj.exercise_type.value if goal_obj.exercise_type else None,
                "exercise_name": goal_obj.exercise_name,
                "targets": [
                    {"target_metric": t.metric.value, "target_value": t.value}
                    for t in goal_obj.targets
                ]
            })

        except Exception as e:
            print(f"❌ Error processing goal: {goal} — {e}")

    return added_goals, repeated_goals




@log_entry_bp.route("/api/log-workout", methods=["POST"])
@jwt_required()
def log_workout():
    user_id = get_jwt_identity()
    raw_text = request.form.get("entry") or request.json.get("entry")
    today_date = datetime.now().strftime("%Y-%m-%d")

    try:
        structured_response = parse_workout_and_goals(raw_text)
        entries = structured_response.get("entries", [])
        goals = structured_response.get("goals", [])
        notes = structured_response.get("notes", "")
        parsed_date = structured_response.get("date")
        valid_entries = [e for e in clean_entries(entries) if "exercise" in e]
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

    session = WorkoutSession(user_id=user_id, date=parsed_date or today_date, raw_text=raw_text, notes=notes)
    db.session.add(session)
    db.session.commit()

    new_prs = []
    if valid_entries:
        for item in valid_entries:
            WorkoutEntry.from_dict(item, session.id)
        db.session.commit()
        new_prs = track_prs_for_session(session, valid_entries)

    added_goals, repeated_goals = process_goals_for_session(goals, user_id, session)

    if added_goals:
        db.session.commit()

    user_goals = Goal.query.filter_by(user_id=user_id).all()
    user_sessions = WorkoutSession.query.filter_by(user_id=user_id).all()
    for goal in user_goals:
        evaluate_goal(goal, user_sessions, session)

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Workout entry created successfully!" if valid_entries else "Workout session created (notes only)",
        "session_id": session.id,
        "session_date": session.date.format(),
        "raw_text": raw_text,
        "new_prs": new_prs,
        "goals_added": len(added_goals),
        "goals": added_goals,
        "repeated_goals": repeated_goals
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
        goals = structured_response.get("goals", [])
        notes = structured_response.get("notes", "")
        parsed_date = structured_response.get("date")
        cleaned_entries = clean_entries(entries)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

    entry_ids = [e.id for e in WorkoutEntry.query.filter_by(session_id=session.id).all()]
    StrengthEntry.query.filter(StrengthEntry.entry_id.in_(entry_ids)).delete(synchronize_session=False)
    CardioEntry.query.filter(CardioEntry.entry_id.in_(entry_ids)).delete(synchronize_session=False)
    WorkoutEntry.query.filter(WorkoutEntry.id.in_(entry_ids)).delete(synchronize_session=False)

    # Delete associated goals and their targets
    goals_to_delete = Goal.query.filter_by(session_id=session.id).all()
    for goal in goals_to_delete:
        GoalTarget.query.filter_by(goal_id=goal.id).delete(synchronize_session=False)
    Goal.query.filter_by(session_id=session.id).delete(synchronize_session=False)

    for item in cleaned_entries:
        WorkoutEntry.from_dict(item, session.id)

    session.raw_text = raw_text
    session.notes = notes
    if parsed_date:
        session.date = parsed_date

    PersonalRecord.query.filter_by(session_id=session.id).delete(synchronize_session=False)
    db.session.flush()
    new_prs = track_prs_for_session(session, cleaned_entries)

    added_goals, repeated_goals = process_goals_for_session(goals, user_id, session, allow_same_session_duplicate=True)
    if added_goals:
        db.session.commit()

    user_goals = Goal.query.filter_by(user_id=user_id).all()
    user_sessions = WorkoutSession.query.filter_by(user_id=user_id).all()
    for goal in user_goals:
        evaluate_goal(goal, user_sessions, session)

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Workout session updated successfully.",
        "session_id": session.id,
        "session_date": session.date.format(),
        "raw_text": raw_text,
        "new_prs": new_prs,
        "goals_added": len(added_goals),
        "goals": added_goals,
        "repeated_goals": repeated_goals
    }), 200
