from init import db
from models import PersonalRecord


def track_prs_for_session(session, entries):
    new_prs = []

    for entry in entries:
        exercise = entry.get("exercise")
        entry_type = entry.get("type")

        if entry_type == "strength":
            sets = entry.get("sets_details", [])
            weights = [s.get("weight") for s in sets if s.get("weight") is not None]
            reps = [s.get("reps") for s in sets if s.get("reps") is not None]

            # Track weight PRs
            if weights:
                max_weight = max(weights)
                new_pr = maybe_record_pr(exercise, "strength", "weight", max_weight, session.id)
                if new_pr:
                    new_prs.append(new_pr)

            # Track rep PRs (only if no weights present)
            if not weights and reps:
                max_reps = max(reps)
                new_pr = maybe_record_pr(exercise, "strength", "reps", max_reps, session.id)
                if new_pr:
                    new_prs.append(new_pr)

        elif entry_type == "cardio":
            distance = entry.get("distance")
            duration = entry.get("duration")

            if distance:
                new_pr = maybe_record_pr(exercise, "cardio", "distance", distance, session.id)
                if new_pr:
                    new_prs.append(new_pr)

            if duration:
                new_pr = maybe_record_pr(exercise, "cardio", "duration", duration, session.id)
                if new_pr:
                    new_prs.append(new_pr)

    db.session.commit()
    return new_prs

def maybe_record_pr(exercise, type_, field, value, session_id):
    previous_pr = (
        db.session.query(PersonalRecord)
        .filter_by(exercise=exercise, type=type_, field=field)
        .order_by(PersonalRecord.value.desc())
        .first()
    )

    if not previous_pr or value > previous_pr.value:
        if previous_pr:
            db.session.delete(previous_pr)

        new_pr = PersonalRecord(
            exercise=exercise,
            type=type_,
            field=field,
            value=value,
            session_id=session_id
        )
        db.session.add(new_pr)
        return {
            "exercise": exercise,
            "type": type_,
            "field": field,
            "value": value
        }

    return None
