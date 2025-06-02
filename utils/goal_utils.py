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
                    total = cardio.pace or 0
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


def entries_meet_conditions(entries, targets, pace_tolerance=0.01):
    min_weight = next((t.value for t in targets if t.metric == MetricEnum.weight), None)
    max_pace = next((t.value for t in targets if t.metric == MetricEnum.pace), None)

    print(f"[DEBUG] Checking {len(entries)} entries with min_weight={min_weight}, max_pace={max_pace}")

    filtered_entries = []
    for entry in entries:
        if entry.type == 'strength':
            valid_sets = []
            for s in entry.strength_entries:
                if min_weight is None or s.weight >= min_weight:
                    valid_sets.append(s)
                    print(f"[DEBUG] Strength set accepted: weight={s.weight} (min required: {min_weight})")
                else:
                    print(f"[DEBUG] Strength set rejected: weight={s.weight} < min required {min_weight}")
            if valid_sets:
                entry.strength_entries = valid_sets
                filtered_entries.append(entry)
                print(f"[INFO] Strength entry accepted with {len(valid_sets)} valid sets")
            else:
                print(f"[INFO] Strength entry rejected (no valid sets)")


        elif entry.type == 'cardio' and entry.cardio_detail:
            pace = entry.cardio_detail.pace
            if max_pace is None:
                filtered_entries.append(entry)
                print(f"[INFO] Cardio entry accepted (no max pace defined)")
            elif pace is not None and pace <= max_pace + pace_tolerance:
                filtered_entries.append(entry)
                print(
                    f"[INFO] Cardio entry accepted: pace={pace:.2f} <= max pace {max_pace:.2f} (+ tolerance {pace_tolerance})")
            else:
                if pace is None:
                    print(
                        f"[INFO] Cardio entry rejected: pace is None (max pace {max_pace}, tolerance {pace_tolerance})")
                else:
                    print(
                        f"[INFO] Cardio entry rejected: pace={pace:.2f} > max pace {max_pace:.2f} (+ tolerance {pace_tolerance})")

    print(f"[RESULT] Total entries accepted: {len(filtered_entries)}")
    return filtered_entries


# -----------------------------
# Evaluation Functions
# -----------------------------

def evaluate_single_session_goal(goal: Goal, session: WorkoutSession):
    session_date = to_date(session.date)
    goal_end_date = to_date(goal.end_date or datetime.utcnow().date())
    print(f"[DEBUG] Evaluating goal {goal.id} for session {session.id} on {session_date}")

    if not (to_date(goal.start_date) <= session_date <= goal_end_date):
        print(f"[INFO] Session date {session_date} is outside goal date range {goal.start_date} to {goal_end_date}")
        return

    entries = get_entries_from_session(session, goal.exercise_type.value, goal.exercise_name)
    if not entries:
        print(f"[INFO] No matching entries found in session {session.id} for goal exercise {goal.exercise_name}")
        return

    filtered_entries = entries_meet_conditions(entries, goal.targets)
    print(f"[DEBUG] {len(filtered_entries)} entries remained after filtering for goal conditions")

    all_targets_met = True
    progress_entries = []

    for target in goal.targets:
        value = extract_metric_from_entries(filtered_entries, target.metric)
        print(f"[DEBUG] Target check: metric={target.metric}, required={target.value}, achieved={value}")

        # Adjust comparison for pace (lower is better)
        if target.metric == MetricEnum.pace:
            condition_met = value <= target.value
        else:
            condition_met = value >= target.value

        if condition_met:
            progress_entries.append(GoalProgress(
                goal_id=goal.id,
                session_id=session.id,
                metric=target.metric,
                value_achieved=value,
                achieved_on=session_date,
                is_complete=True
            ))
        else:
            print(f"[INFO] Target not met: {target.metric} required {target.value}, got {value}")
            all_targets_met = False
            break

    if all_targets_met:
        print(f"[SUCCESS] All targets met for goal {goal.id} in session {session.id}")
        for p in progress_entries:
            db.session.add(p)
    else:
        print(f"[INFO] Goal {goal.id} not completed in session {session.id}")




def evaluate_aggregate_goal(goal: Goal, sessions: list[WorkoutSession]):
    relevant_sessions = filter_sessions_by_type_and_date(
        sessions, goal.exercise_type.value, goal.start_date, goal.end_date or datetime.utcnow().date()
    )

    all_entries = []
    for s in relevant_sessions:
        session_entries = get_entries_from_session(s, goal.exercise_type.value, goal.exercise_name)
        all_entries.extend(entries_meet_conditions(session_entries, goal.targets))

    for target in goal.targets:
        total = extract_metric_from_entries(all_entries, target.metric)
        is_complete = total >= target.value

        db.session.add(GoalProgress(
            goal_id=goal.id,
            session_id=None,
            metric=target.metric,
            value_achieved=total,
            achieved_on=datetime.utcnow().date(),
            is_complete=is_complete
        ))


def evaluate_general_aggregate_goal(goal: Goal, sessions: list[WorkoutSession]):
    filtered_sessions = filter_sessions_by_type_and_date(
        sessions, goal.exercise_type.value, goal.start_date, goal.end_date or datetime.utcnow().date()
    )

    for target in goal.targets:
        if target.metric == MetricEnum.sessions:
            count = len(filtered_sessions)
            is_complete = count >= target.value

            db.session.add(GoalProgress(
                goal_id=goal.id,
                session_id=None,
                metric=target.metric,
                value_achieved=count,
                achieved_on=datetime.utcnow().date(),
                is_complete=is_complete
            ))


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

# -----------------------------
# Serialization
# -----------------------------

def serialize_goal(goal):
    return {
        "id": goal.id,
        "user_id": goal.user_id,
        "name": goal.name,
        "description": goal.description,
        "start_date": goal.start_date.isoformat(),
        "end_date": goal.end_date.isoformat() if goal.end_date else None,
        "goal_type": goal.goal_type.value,
        "exercise_type": goal.exercise_type.value if goal.exercise_type else None,
        "exercise_name": goal.exercise_name,
        "created_at": goal.created_at.isoformat() if goal.created_at else None,
        "updated_at": goal.updated_at.isoformat() if goal.updated_at else None,
    }

def serialize_target(target):
    return {
        "id": target.id,
        "goal_id": target.goal_id,
        "metric": target.metric.value,
        "value": target.value,
    }

def serialize_progress(progress):
    return {
        "id": progress.id,
        "goal_id": progress.goal_id,
        "session_id": progress.session_id,
        "metric": progress.metric.value,
        "value_achieved": progress.value_achieved,
        "is_complete": progress.is_complete,
        "achieved_on": progress.achieved_on.isoformat(),
    }
