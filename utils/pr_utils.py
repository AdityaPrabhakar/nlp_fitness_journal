from init import db
from models import PersonalRecord, WorkoutEntry, StrengthEntry, CardioEntry, WorkoutSession


def track_prs_for_session(session, entries):
    """
    Tracks new personal records for the given workout session and list of entries.
    Returns a list of new PRs triggered by this session.
    """
    new_prs = []
    user_id = session.user_id

    for entry in entries:
        exercise = entry.get("exercise")
        entry_type = entry.get("type")

        if entry_type == "strength":
            sets = entry.get("sets_details", [])
            weights = [s.get("weight") for s in sets if s.get("weight") is not None]
            reps = [s.get("reps") for s in sets if s.get("reps") is not None]

            if weights:
                max_weight = max(weights)
                new_pr = update_pr_record(user_id, exercise, "strength", "weight", max_weight, session.id)
                if new_pr:
                    new_prs.append(new_pr)

            if not weights and reps:
                max_reps = max(reps)
                new_pr = update_pr_record(user_id, exercise, "strength", "reps", max_reps, session.id)
                if new_pr:
                    new_prs.append(new_pr)

        elif entry_type == "cardio":
            distance = entry.get("distance")
            duration = entry.get("duration")

            if distance:
                new_pr = update_pr_record(user_id, exercise, "cardio", "distance", distance, session.id)
                if new_pr:
                    new_prs.append(new_pr)

            if duration:
                new_pr = update_pr_record(user_id, exercise, "cardio", "duration", duration, session.id)
                if new_pr:
                    new_prs.append(new_pr)

    db.session.commit()
    return new_prs


def update_pr_record(user_id, exercise, type_, field, current_value, current_session_id):
    """
    Recalculates and updates the top personal record for the given user, exercise, type, and field.
    Returns the new PR dict if the current session created it, otherwise None.
    """

    # Delete existing PR for this user/exercise/type/field
    db.session.query(PersonalRecord).filter_by(
        user_id=user_id,
        exercise=exercise,
        type=type_,
        field=field
    ).delete()

    # Query the highest value for this field, scoped to the current user
    if type_ == "strength":
        if field == "weight":
            query = (
                db.session.query(StrengthEntry.weight, WorkoutEntry.session_id)
                .join(WorkoutEntry, StrengthEntry.entry_id == WorkoutEntry.id)
                .join(WorkoutSession, WorkoutEntry.session_id == WorkoutSession.id)
                .filter(
                    WorkoutEntry.exercise == exercise,
                    StrengthEntry.weight != None,
                    WorkoutSession.user_id == user_id
                )
                .order_by(StrengthEntry.weight.desc())
            )
        elif field == "reps":
            query = (
                db.session.query(StrengthEntry.reps, WorkoutEntry.session_id)
                .join(WorkoutEntry, StrengthEntry.entry_id == WorkoutEntry.id)
                .join(WorkoutSession, WorkoutEntry.session_id == WorkoutSession.id)
                .filter(
                    WorkoutEntry.exercise == exercise,
                    StrengthEntry.reps != None,
                    StrengthEntry.weight == None,
                    WorkoutSession.user_id == user_id
                )
                .order_by(StrengthEntry.reps.desc())
            )
        else:
            return None

    elif type_ == "cardio":
        if field == "distance":
            query = (
                db.session.query(CardioEntry.distance, WorkoutEntry.session_id)
                .join(WorkoutEntry, CardioEntry.entry_id == WorkoutEntry.id)
                .join(WorkoutSession, WorkoutEntry.session_id == WorkoutSession.id)
                .filter(
                    WorkoutEntry.exercise == exercise,
                    CardioEntry.distance != None,
                    WorkoutSession.user_id == user_id
                )
                .order_by(CardioEntry.distance.desc())
            )
        elif field == "duration":
            query = (
                db.session.query(CardioEntry.duration, WorkoutEntry.session_id)
                .join(WorkoutEntry, CardioEntry.entry_id == WorkoutEntry.id)
                .join(WorkoutSession, WorkoutEntry.session_id == WorkoutSession.id)
                .filter(
                    WorkoutEntry.exercise == exercise,
                    CardioEntry.duration != None,
                    WorkoutSession.user_id == user_id
                )
                .order_by(CardioEntry.duration.desc())
            )
        else:
            return None

    else:
        return None

    top_record = query.first()

    if top_record:
        value, session_id = top_record

        # Save the new PR
        db.session.add(PersonalRecord(
            user_id=user_id,
            exercise=exercise,
            type=type_,
            field=field,
            value=value,
            session_id=session_id
        ))

        # Only return the PR if it was caused by the current session
        if session_id == current_session_id and current_value == value:
            return {
                "exercise": exercise,
                "type": type_,
                "field": field,
                "value": value,
                "session_id": session_id
            }

    return None
