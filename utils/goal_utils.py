from datetime import datetime, date

from sqlalchemy import desc

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
                    total = set_data.weight
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

def progress_has_changed(goal_id: int, metric: MetricEnum, new_value: float) -> bool:
    from sqlalchemy import and_, desc

    if isinstance(metric, str):
        try:
            metric = MetricEnum(metric)
        except ValueError:
            raise ValueError(f"Invalid metric string: {metric}")

    print(f"\n[progress_has_changed] START — goal_id={goal_id}, metric={metric.name}, new_value={new_value}")

    query = GoalProgress.query.filter(
        and_(
            GoalProgress.goal_id == goal_id,
            GoalProgress.metric == metric.value
        )
    ).order_by(desc(GoalProgress.achieved_on), desc(GoalProgress.id))

    print(f"[progress_has_changed] Query: goal_id={goal_id}, metric={metric.value}")

    previous_progress = query.first()

    if not previous_progress:
        print("[progress_has_changed] No previous progress found. Returning True.")
        return True

    print(f"[progress_has_changed] Fetched GoalProgress row:")
    print(f"  ID: {previous_progress.id}")
    print(f"  Goal ID: {previous_progress.goal_id}")
    print(f"  Metric: {previous_progress.metric}")
    print(f"  Achieved On: {previous_progress.achieved_on}")
    print(f"  Value Achieved: {previous_progress.value_achieved} (type={type(previous_progress.value_achieved)})")

    has_changed = previous_progress.value_achieved != new_value
    print(f"[progress_has_changed] Value changed? {has_changed} (prev={previous_progress.value_achieved}, new={new_value})")

    print(f"[progress_has_changed] END\n")
    return has_changed




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

        if target.metric == MetricEnum.pace:
            condition_met = value <= target.value
        else:
            condition_met = value >= target.value

        if condition_met:
            if progress_has_changed(goal.id, target.metric, value):
                progress_entries.append(GoalProgress(
                    goal_id=goal.id,
                    session_id=session.id,
                    metric=target.metric,
                    value_achieved=value,
                    achieved_on=session_date,
                    is_complete=True
                ))
            else:
                print(f"[INFO] No change in progress for {target.metric}, skipping entry.")
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

        if target.metric == MetricEnum.pace:
            # Guard against invalid or missing pace values
            if total > 0:
                is_complete = total <= target.value
            else:
                is_complete = False
        else:
            is_complete = total >= target.value

        if progress_has_changed(goal.id, target.metric, total):
            db.session.add(GoalProgress(
                goal_id=goal.id,
                session_id=None,
                metric=target.metric,
                value_achieved=total,
                achieved_on=datetime.utcnow().date(),
                is_complete=is_complete
            ))
        else:
            print(f"[INFO] No change in aggregate progress for {target.metric}, skipping entry.")


def evaluate_general_aggregate_goal(goal: Goal, sessions: list[WorkoutSession]):
    print(f"[DEBUG] Evaluating general aggregate goal {goal.id} for exercise {goal.exercise_name}")

    filtered_sessions = filter_sessions_by_type_and_date(
        sessions, goal.exercise_type.value, goal.start_date, goal.end_date or datetime.utcnow().date()
    )
    print(f"[DEBUG] Found {len(filtered_sessions)} relevant sessions for goal {goal.id} between {goal.start_date} and {goal.end_date or datetime.utcnow().date()}")

    for target in goal.targets:
        if target.metric == MetricEnum.sessions:
            count = len(filtered_sessions)
            is_complete = count >= target.value

            print(f"[DEBUG] Target check: metric=sessions, required={target.value}, achieved={count}, is_complete={is_complete}")

            if progress_has_changed(goal.id, 'sessions', count):
                print(f"[SUCCESS] New session count progress for goal {goal.id}: {count} sessions. Creating GoalProgress.")
                db.session.add(GoalProgress(
                    goal_id=goal.id,
                    session_id=None,
                    metric=target.metric,
                    value_achieved=count,
                    achieved_on=datetime.utcnow().date(),
                    is_complete=is_complete
                ))
            else:
                print(f"[INFO] No change in session count for goal {goal.id}, skipping GoalProgress entry.")



# -----------------------------
# Orchestration Function
# -----------------------------

def evaluate_goal(goal: Goal, user_sessions: list[WorkoutSession], current_session: WorkoutSession = None):
    # ✅ Check if any GoalProgress entry marks this goal as complete
    completed_progress = next((p for p in sorted(goal.progress, key=lambda p: p.achieved_on, reverse=True) if p.is_complete), None)
    if completed_progress:
        return  # Goal already completed; skip further evaluation

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
