from datetime import datetime, date
from models import Goal, GoalProgress, MetricEnum, GoalTypeEnum
from models import WorkoutSession, WorkoutEntry, StrengthEntry, CardioEntry
from init import db


# -----------------------------
# Utility Functions
# -----------------------------

def get_entries_from_session(session, exercise_type, exercise_name=None):
    entries = []
    for entry in session.entries:
        if exercise_type and entry.type != exercise_type:
            continue
        if exercise_name and entry.exercise != exercise_name:
            continue
        entries.append(entry)
    return entries


def extract_metric_from_entries(entries, metric):
    total = 0
    for entry in entries:
        if entry.type == 'strength':
            for set_data in entry.strength_entries:
                if metric == MetricEnum.reps:
                    total += set_data.reps
                elif metric == MetricEnum.sets:
                    total += 1
                elif metric == MetricEnum.weight:
                    total += set_data.weight
        elif entry.type == 'cardio':
            cardio = entry.cardio_detail
            if cardio:
                if metric == MetricEnum.distance:
                    total += cardio.distance or 0
                elif metric == MetricEnum.duration:
                    total += cardio.duration or 0
                elif metric == MetricEnum.pace:
                    total += cardio.pace or 0
    return total


def to_date(d):
    if isinstance(d, date):
        return d
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, str):
        return datetime.strptime(d, "%Y-%m-%d").date()
    raise ValueError(f"Unsupported date format: {d} (type: {type(d)})")



def filter_sessions_by_type_and_date(sessions, exercise_type, start_date, end_date):
    start_date = to_date(start_date)
    end_date = to_date(end_date)

    return [
        s for s in sessions
        if start_date <= to_date(s.date) <= end_date and (
            exercise_type == 'general' or any(e.type == exercise_type for e in s.entries)
        )
    ]


def filter_entries_by_exercise(entries, exercise_type, exercise_name):
    return [
        e for e in entries
        if e.type == exercise_type and (exercise_name is None or e.exercise_name == exercise_name)
    ]


# -----------------------------
# Evaluation Functions
# -----------------------------

def evaluate_single_session_goal(goal: Goal, session: WorkoutSession):
    session_date = to_date(session.date)

    if not (to_date(goal.start_date) <= session_date <= to_date(goal.end_date or datetime.utcnow().date())):
        return

    entries = get_entries_from_session(session, goal.exercise_type.value, goal.exercise_name)
    if not entries:
        return

    all_targets_met = True
    for target in goal.targets:
        value = extract_metric_from_entries(entries, target.metric)
        if value >= target.value:
            progress = GoalProgress(
                goal_id=goal.id,
                session_id=session.id,
                metric=target.metric,
                value_achieved=value,
                achieved_on=session_date,
                is_complete=True
            )
            db.session.add(progress)
        else:
            all_targets_met = False

    return all_targets_met



def evaluate_aggregate_goal(goal: Goal, sessions: list[WorkoutSession]):
    relevant_sessions = filter_sessions_by_type_and_date(
        sessions, goal.exercise_type.value, goal.start_date, goal.end_date or datetime.utcnow().date()
    )
    entries = []
    for s in relevant_sessions:
        entries.extend(get_entries_from_session(s, goal.exercise_type.value, goal.exercise_name))

    for target in goal.targets:
        total = extract_metric_from_entries(entries, target.metric)
        is_complete = total >= target.value

        progress = GoalProgress(
            goal_id=goal.id,
            session_id=None,
            metric=target.metric,
            value_achieved=total,
            achieved_on=datetime.utcnow().date(),
            is_complete=is_complete
        )
        db.session.add(progress)


def evaluate_general_aggregate_goal(goal: Goal, sessions: list[WorkoutSession]):
    filtered_sessions = filter_sessions_by_type_and_date(
        sessions, goal.exercise_type.value, goal.start_date, goal.end_date or datetime.utcnow().date()
    )

    for target in goal.targets:
        if target.metric == MetricEnum.sessions:
            count = len(filtered_sessions)
            is_complete = count >= target.value

            progress = GoalProgress(
                goal_id=goal.id,
                session_id=None,
                metric=target.metric,
                value_achieved=count,
                achieved_on=datetime.utcnow().date(),
                is_complete=is_complete
            )
            db.session.add(progress)


# -----------------------------
# Orchestration Function
# -----------------------------

def evaluate_goal(goal: Goal, user_sessions: list[WorkoutSession], current_session: WorkoutSession = None):
    if goal.goal_type == GoalTypeEnum.single_session:
        if current_session:
            evaluate_single_session_goal(goal, current_session)
    elif goal.goal_type == GoalTypeEnum.aggregate:
        if goal.exercise_name:
            evaluate_aggregate_goal(goal, user_sessions)
        else:
            evaluate_general_aggregate_goal(goal, user_sessions)
