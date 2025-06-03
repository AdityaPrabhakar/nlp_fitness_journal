from flask import Blueprint, jsonify, request, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity

from models.goal import Goal, GoalTarget, GoalProgress, MetricEnum, GoalTypeEnum
from init import db
from sqlalchemy import or_

from utils import serialize_goal, serialize_progress, serialize_target

goal_bp = Blueprint("goal", __name__)

@goal_bp.route("/api/goals/dashboard")
def goals_dashboard():
    return render_template("partials/goals.html")


# --- Get All Goals (with optional filters) ---
@goal_bp.route("/api/goals", methods=["GET"])
@jwt_required()
def get_goals():
    user_id = get_jwt_identity()

    goal_type = request.args.get("goal_type")
    exercise_type = request.args.get("exercise_type")
    active_only = request.args.get("active") == "true"

    query = Goal.query.filter_by(user_id=user_id)

    if goal_type:
        query = query.filter(Goal.goal_type == GoalTypeEnum(goal_type))
    if exercise_type:
        query = query.filter(Goal.exercise_type == exercise_type)
    if active_only:
        from datetime import date
        today = date.today()
        query = query.filter(or_(Goal.end_date == None, Goal.end_date >= today))

    goals = query.all()
    return jsonify([serialize_goal(g) for g in goals])


# --- Get All Progress for a Given Goal ---
@goal_bp.route("/api/goals/<int:goal_id>/progress", methods=["GET"])
@jwt_required()
def get_goal_progress(goal_id):
    # Note: No user ID check is performed here — consider verifying goal ownership for security
    metric = request.args.get("metric")

    query = GoalProgress.query.filter_by(goal_id=goal_id)
    if metric:
        query = query.filter(GoalProgress.metric == MetricEnum(metric))

    progress = query.order_by(GoalProgress.achieved_on.asc()).all()
    return jsonify([serialize_progress(p) for p in progress])


# --- Get Goals + All Targets + Progress (Optionally Filtered by Exercise Name) ---
@goal_bp.route("/api/goals/with-progress", methods=["GET"])
@jwt_required()
def get_goals_with_progress():
    user_id = get_jwt_identity()
    exercise_name = request.args.get("exercise")

    # Fetch all goals for the user
    goals = Goal.query.filter_by(user_id=user_id).all()
    result = []

    for g in goals:
        # If filtering by exercise name, match against the goal's exercise_name
        if exercise_name and g.exercise_name != exercise_name:
            continue  # Skip goals not matching the exercise name

        data = serialize_goal(g)
        data["targets"] = [serialize_target(t) for t in g.targets]
        data["progress"] = [serialize_progress(p) for p in g.progress]
        result.append(data)

    return jsonify(result)



# --- Delete a Goal ---
@goal_bp.route("/api/goals/<int:goal_id>", methods=["DELETE"])
@jwt_required()
def delete_goal(goal_id):
    user_id = get_jwt_identity()

    goal = Goal.query.filter_by(id=goal_id, user_id=user_id).first()
    if not goal:
        return jsonify({"error": "Goal not found or unauthorized"}), 404

    # Optionally: delete related targets and progress if not set up to cascade
    for target in goal.targets:
        db.session.delete(target)
    for progress in goal.progress:
        db.session.delete(progress)

    db.session.delete(goal)
    db.session.commit()

    return jsonify({"message": "Goal deleted successfully"}), 200

