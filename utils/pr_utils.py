from datetime import datetime
from init import db
from models import PersonalRecord, WorkoutEntry, StrengthEntry, CardioEntry, WorkoutSession

def track_prs_for_session(session, entries):
    new_prs = []
    user_id = session.user_id

    # Combine date and time into a single datetime object
    session_date_obj = session.date
    session_datetime = datetime.combine(session_date_obj, session.time)

    for entry in entries:
        exercise = entry.get("exercise")
        entry_type = entry.get("type")

        if entry_type == "strength":
            sets = entry.get("sets_details", [])
            weights = [s.get("weight") for s in sets if s.get("weight") is not None]
            reps = [s.get("reps") for s in sets if s.get("reps") is not None]

            if weights:
                max_weight = max(weights)
                new_pr = update_pr_record(user_id, exercise, "strength", "weight", max_weight, session.id, session_datetime, "lbs")
                if new_pr:
                    new_prs.append(new_pr)

            if not weights and reps:
                max_reps = max(reps)
                new_pr = update_pr_record(user_id, exercise, "strength", "reps", max_reps, session.id, session_datetime, "reps")
                if new_pr:
                    new_prs.append(new_pr)

        elif entry_type == "cardio":
            distance = entry.get("distance")
            duration = entry.get("duration")
            pace = entry.get("pace")

            if distance:
                new_pr = update_pr_record(user_id, exercise, "cardio", "distance", distance, session.id, session_datetime, "mi")
                if new_pr:
                    new_prs.append(new_pr)

            if duration:
                new_pr = update_pr_record(user_id, exercise, "cardio", "duration", duration, session.id, session_datetime, "min")
                if new_pr:
                    new_prs.append(new_pr)

            if pace:
                new_pr = update_pr_record(user_id, exercise, "cardio", "pace", pace, session.id, session_datetime, "min/mi")
                if new_pr:
                    new_prs.append(new_pr)

    db.session.commit()
    return new_prs


from datetime import datetime
from init import db
from models import PersonalRecord, WorkoutEntry, StrengthEntry, CardioEntry, WorkoutSession

def update_pr_record(user_id, exercise, type_, field, current_value, current_session_id, session_datetime, units):
    previous_sessions = (
        db.session.query(WorkoutSession.id)
        .filter(WorkoutSession.user_id == user_id)
        .all()
    )

    session_id_map = {}
    for sid, in previous_sessions:
        s = db.session.query(WorkoutSession).get(sid)
        if not s or not s.date:
            continue
        try:
            session_date = s.date
            if s.time:
                s_datetime = datetime.combine(session_date, s.time)
                if s_datetime < session_datetime:
                    session_id_map[sid] = s_datetime
            else:
                # Compare by date only if time is missing
                if session_date < session_datetime.date():
                    session_id_map[sid] = datetime.combine(session_date, datetime.min.time())
        except Exception:
            continue

    if not session_id_map:
        # No prior session → automatically a PR
        db.session.add(PersonalRecord(
            user_id=user_id,
            exercise=exercise,
            type=type_,
            field=field,
            value=current_value,
            units=units,
            session_id=current_session_id,
            datetime=session_datetime
        ))
        return {
            "exercise": exercise,
            "type": type_,
            "field": field,
            "value": current_value,
            "units": units,
            "session_id": current_session_id
        }

    # Build comparison query
    if type_ == "strength":
        if field == "weight":
            query = db.session.query(StrengthEntry.weight, WorkoutEntry.session_id).join(
                WorkoutEntry, StrengthEntry.entry_id == WorkoutEntry.id
            ).filter(
                WorkoutEntry.exercise == exercise,
                StrengthEntry.weight != None,
                WorkoutEntry.session_id.in_(session_id_map.keys())
            )
        elif field == "reps":
            query = db.session.query(StrengthEntry.reps, WorkoutEntry.session_id).join(
                WorkoutEntry, StrengthEntry.entry_id == WorkoutEntry.id
            ).filter(
                WorkoutEntry.exercise == exercise,
                StrengthEntry.reps != None,
                StrengthEntry.weight == None,
                WorkoutEntry.session_id.in_(session_id_map.keys())
            )
        else:
            return None
    elif type_ == "cardio":
        if field == "distance":
            query = db.session.query(CardioEntry.distance, WorkoutEntry.session_id).join(
                WorkoutEntry, CardioEntry.entry_id == WorkoutEntry.id
            ).filter(
                WorkoutEntry.exercise == exercise,
                CardioEntry.distance != None,
                WorkoutEntry.session_id.in_(session_id_map.keys())
            )
        elif field == "duration":
            query = db.session.query(CardioEntry.duration, WorkoutEntry.session_id).join(
                WorkoutEntry, CardioEntry.entry_id == WorkoutEntry.id
            ).filter(
                WorkoutEntry.exercise == exercise,
                CardioEntry.duration != None,
                WorkoutEntry.session_id.in_(session_id_map.keys())
            )
        elif field == "pace":
            query = db.session.query(CardioEntry.pace, WorkoutEntry.session_id).join(
                WorkoutEntry, CardioEntry.entry_id == WorkoutEntry.id
            ).filter(
                WorkoutEntry.exercise == exercise,
                CardioEntry.pace != None,
                WorkoutEntry.session_id.in_(session_id_map.keys())
            )
        else:
            return None
    else:
        return None

    all_previous_values = query.all()

    if all_previous_values:
        if field == "pace":
            is_better = all(current_value < v for v, _ in all_previous_values if v is not None)
        else:
            is_better = all(current_value > v for v, _ in all_previous_values if v is not None)

        if not is_better:
            return None

    db.session.add(PersonalRecord(
        user_id=user_id,
        exercise=exercise,
        type=type_,
        field=field,
        value=current_value,
        units=units,
        session_id=current_session_id,
        datetime=session_datetime
    ))
    return {
        "exercise": exercise,
        "type": type_,
        "field": field,
        "value": current_value,
        "units": units,
        "session_id": current_session_id
    }
