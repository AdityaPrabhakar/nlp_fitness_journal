from init import db
from sqlalchemy import func
from models import PersonalRecord, WorkoutEntry, StrengthEntry, CardioEntry


def track_prs_for_session(session, entries):
    new_prs = []
    exercises_updated = set()

    for entry in entries:
        exercise = entry.get("exercise")
        entry_type = entry.get("type")
        exercises_updated.add((exercise, entry_type))

        if entry_type == "strength":
            sets = entry.get("sets_details", [])
            weights = [s.get("weight") for s in sets if s.get("weight") is not None]
            reps = [s.get("reps") for s in sets if s.get("reps") is not None]

            if weights:
                max_weight = max(weights)
                new_pr = update_pr_record(exercise, "strength", "weight", max_weight, session.id)
                if new_pr and new_pr["session_id"] == session.id:
                    new_prs.append(new_pr)

            if not weights and reps:
                max_reps = max(reps)
                new_pr = update_pr_record(exercise, "strength", "reps", max_reps, session.id)
                if new_pr and new_pr["session_id"] == session.id:
                    new_prs.append(new_pr)

        elif entry_type == "cardio":
            distance = entry.get("distance")
            duration = entry.get("duration")

            if distance:
                new_pr = update_pr_record(exercise, "cardio", "distance", distance, session.id)
                if new_pr and new_pr["session_id"] == session.id:
                    new_prs.append(new_pr)

            if duration:
                new_pr = update_pr_record(exercise, "cardio", "duration", duration, session.id)
                if new_pr and new_pr["session_id"] == session.id:
                    new_prs.append(new_pr)

    db.session.commit()
    return new_prs

def update_pr_record(exercise, type_, field, current_value, current_session_id):
    """
    Always updates the PersonalRecord to reflect the actual top performance
    across all sessions. Only returns a PR if the current session holds it.
    """
    # Remove existing PR for this field/exercise/type
    db.session.query(PersonalRecord).filter_by(
        exercise=exercise,
        type=type_,
        field=field
    ).delete()

    # Determine new top PR value and its session
    if type_ == "strength":
        if field == "weight":
            query = (
                db.session.query(StrengthEntry.weight, WorkoutEntry.session_id)
                .join(WorkoutEntry, StrengthEntry.entry_id == WorkoutEntry.id)
                .filter(WorkoutEntry.exercise == exercise, StrengthEntry.weight != None)
                .order_by(StrengthEntry.weight.desc())
            )
        elif field == "reps":
            query = (
                db.session.query(StrengthEntry.reps, WorkoutEntry.session_id)
                .join(WorkoutEntry, StrengthEntry.entry_id == WorkoutEntry.id)
                .filter(WorkoutEntry.exercise == exercise,
                        StrengthEntry.weight == None,
                        StrengthEntry.reps != None)
                .order_by(StrengthEntry.reps.desc())
            )
    elif type_ == "cardio":
        if field == "distance":
            query = (
                db.session.query(CardioEntry.distance, WorkoutEntry.session_id)
                .join(WorkoutEntry, CardioEntry.entry_id == WorkoutEntry.id)
                .filter(WorkoutEntry.exercise == exercise, CardioEntry.distance != None)
                .order_by(CardioEntry.distance.desc())
            )
        elif field == "duration":
            query = (
                db.session.query(CardioEntry.duration, WorkoutEntry.session_id)
                .join(WorkoutEntry, CardioEntry.entry_id == WorkoutEntry.id)
                .filter(WorkoutEntry.exercise == exercise, CardioEntry.duration != None)
                .order_by(CardioEntry.duration.desc())
            )
    else:
        return None

    top_record = query.first()

    if top_record:
        value, session_id = top_record
        db.session.add(PersonalRecord(
            exercise=exercise,
            type=type_,
            field=field,
            value=value,
            session_id=session_id
        ))

        # Only return it if this session caused the PR
        if session_id == current_session_id and current_value == value:
            return {
                "exercise": exercise,
                "type": type_,
                "field": field,
                "value": value,
                "session_id": session_id
            }

    return None
