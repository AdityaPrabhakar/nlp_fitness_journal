from datetime import datetime
from init import db
from models import PersonalRecord, WorkoutEntry, StrengthEntry, CardioEntry, WorkoutSession

def track_prs_for_session(session, entries):
    new_prs = []
    user_id = session.user_id
    session_date_str = session.date  # assumed to be a string like "2025-05-28"

    for entry in entries:
        exercise = entry.get("exercise")
        entry_type = entry.get("type")

        if entry_type == "strength":
            sets = entry.get("sets_details", [])
            weights = [s.get("weight") for s in sets if s.get("weight") is not None]
            reps = [s.get("reps") for s in sets if s.get("reps") is not None]

            if weights:
                max_weight = max(weights)
                new_pr = update_pr_record(user_id, exercise, "strength", "weight", max_weight, session.id, session_date_str, "lbs")
                if new_pr:
                    new_prs.append(new_pr)

            if not weights and reps:
                max_reps = max(reps)
                new_pr = update_pr_record(user_id, exercise, "strength", "reps", max_reps, session.id, session_date_str, "reps")
                if new_pr:
                    new_prs.append(new_pr)

        elif entry_type == "cardio":
            distance = entry.get("distance")
            duration = entry.get("duration")
            pace = entry.get("pace")

            if distance:
                new_pr = update_pr_record(user_id, exercise, "cardio", "distance", distance, session.id, session_date_str, "mi")
                if new_pr:
                    new_prs.append(new_pr)

            if duration:
                new_pr = update_pr_record(user_id, exercise, "cardio", "duration", duration, session.id, session_date_str, "min")
                if new_pr:
                    new_prs.append(new_pr)

            if pace:
                new_pr = update_pr_record(user_id, exercise, "cardio", "pace", pace, session.id, session_date_str, "min/mi")
                if new_pr:
                    new_prs.append(new_pr)

    db.session.commit()
    return new_prs


def update_pr_record(user_id, exercise, type_, field, current_value, current_session_id, session_date_str, units):
    timestamp = datetime.strptime(session_date_str, "%Y-%m-%d")

    session_date_filter = WorkoutSession.date < session_date_str  # compare as strings (ISO format)

    if type_ == "strength":
        if field == "weight":
            query = (
                db.session.query(StrengthEntry.weight, WorkoutEntry.session_id)
                .join(WorkoutEntry, StrengthEntry.entry_id == WorkoutEntry.id)
                .join(WorkoutSession, WorkoutEntry.session_id == WorkoutSession.id)
                .filter(
                    WorkoutEntry.exercise == exercise,
                    StrengthEntry.weight != None,
                    WorkoutSession.user_id == user_id,
                    session_date_filter
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
                    WorkoutSession.user_id == user_id,
                    session_date_filter
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
                    WorkoutSession.user_id == user_id,
                    session_date_filter
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
                    WorkoutSession.user_id == user_id,
                    session_date_filter
                )
                .order_by(CardioEntry.duration.desc())
            )
        elif field == "pace":
            query = (
                db.session.query(CardioEntry.pace, WorkoutEntry.session_id)
                .join(WorkoutEntry, CardioEntry.entry_id == WorkoutEntry.id)
                .join(WorkoutSession, WorkoutEntry.session_id == WorkoutSession.id)
                .filter(
                    WorkoutEntry.exercise == exercise,
                    CardioEntry.pace != None,
                    WorkoutSession.user_id == user_id,
                    session_date_filter
                )
                .order_by(CardioEntry.pace.asc())  # lower pace = better
            )
        else:
            return None
    else:
        return None

    top_record = query.first()

    if top_record:
        value, session_id = top_record

        # Only create a new PR if current value is strictly better than previous
        is_new_pr = False
        if field == "pace":
            is_new_pr = current_value < value  # lower pace is better
        else:
            is_new_pr = current_value > value  # higher is better for all others

        if is_new_pr:
            db.session.add(PersonalRecord(
                user_id=user_id,
                exercise=exercise,
                type=type_,
                field=field,
                value=current_value,
                units=units,
                session_id=current_session_id,
                datetime=timestamp
            ))
            return {
                "exercise": exercise,
                "type": type_,
                "field": field,
                "value": current_value,
                "units": units,
                "session_id": current_session_id
            }

    # If no previous record at all, create a new PR
    elif current_value is not None:
        db.session.add(PersonalRecord(
            user_id=user_id,
            exercise=exercise,
            type=type_,
            field=field,
            value=current_value,
            units=units,
            session_id=current_session_id,
            datetime=timestamp
        ))
        return {
            "exercise": exercise,
            "type": type_,
            "field": field,
            "value": current_value,
            "units": units,
            "session_id": current_session_id
        }

    return None
