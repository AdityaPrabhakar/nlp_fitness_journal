from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import WorkoutEntry, WorkoutSession, StrengthEntry, CardioEntry
from init import db

exercise_bp = Blueprint("exercise", __name__)

@exercise_bp.route("/api/exercises/<exercise_type>")
@jwt_required()
def get_exercises_by_type(exercise_type):
    if exercise_type not in ["cardio", "strength"]:
        return jsonify([]), 400

    user_id = get_jwt_identity()

    exercises = (
        db.session.query(WorkoutEntry.exercise)
        .join(WorkoutSession)  # Join WorkoutEntry.session (WorkoutSession)
        .filter(
            WorkoutEntry.type == exercise_type,
            WorkoutSession.user_id == user_id
        )
        .distinct()
        .all()
    )

    return jsonify([e[0] for e in exercises])

@exercise_bp.route("/api/exercise-data/<string:exercise_name>")
@jwt_required()
def get_exercise_data(exercise_name):
    user_id = get_jwt_identity()
    print(f"[INFO] Fetching exercise data for user {user_id}, exercise '{exercise_name}'")

    # Fetch strength entries
    strength_results = (
        db.session.query(StrengthEntry, WorkoutSession.date)
        .join(WorkoutEntry, StrengthEntry.entry_id == WorkoutEntry.id)
        .join(WorkoutSession, WorkoutEntry.session_id == WorkoutSession.id)
        .filter(
            WorkoutEntry.exercise == exercise_name,
            WorkoutSession.user_id == user_id
        )
        .all()
    )
    print(f"[INFO] Found {len(strength_results)} strength entries")

    # Fetch cardio entries
    cardio_results = (
        db.session.query(CardioEntry, WorkoutSession.date)
        .join(WorkoutEntry, CardioEntry.entry_id == WorkoutEntry.id)
        .join(WorkoutSession, WorkoutEntry.session_id == WorkoutSession.id)
        .filter(
            WorkoutEntry.exercise == exercise_name,
            WorkoutSession.user_id == user_id
        )
        .all()
    )
    print(f"[INFO] Found {len(cardio_results)} cardio entries")

    def estimate_1rm(weight, reps):
        if weight is None or reps is None or reps == 0:
            return None
        return weight * (1 + reps / 30)

    def get_intensity_multiplier(intensity):
        if intensity >= 0.9:
            return 1.5
        elif intensity >= 0.8:
            return 1.2
        elif intensity >= 0.7:
            return 1.0
        elif intensity >= 0.6:
            return 0.7
        else:
            return 0.4

    one_rms = [
        estimate_1rm(s.weight, s.reps)
        for s, _ in strength_results
        if s.weight is not None and s.reps is not None
    ]
    max_1rm = max(one_rms) if one_rms else None
    print(f"[INFO] Max 1RM for '{exercise_name}': {max_1rm}")

    data = []

    for s, date in strength_results:
        sets = 1
        reps = s.reps
        weight = s.weight

        if weight is not None and reps is not None and max_1rm:
            intensity = weight / max_1rm
            multiplier = get_intensity_multiplier(intensity)
            effort = sets * reps * weight * multiplier
            print(f"[STRENGTH] {date}: reps={reps}, weight={weight}, intensity={intensity:.2f}, multiplier={multiplier}, effort={effort:.2f}")
        elif weight is None and reps is not None:
            effort = sets * reps * 5  # fallback effort estimate
            print(f"[STRENGTH] {date}: bodyweight fallback, reps={reps}, effort={effort}")
        else:
            effort = None
            print(f"[WARNING] {date}: Skipped strength entry (reps={reps}, weight={weight})")

        data.append({
            "type": "strength",
            "date": date,
            "reps": reps,
            "weight": weight,
            "sets": sets,
            "estimated_1rm": estimate_1rm(weight, reps) if reps and weight else None,
            "effort": effort
        })

    for c, date in cardio_results:
        if c.distance and c.duration:
            speed = c.distance / (c.duration / 60)
            effort = c.distance * speed**1.2
            print(f"[CARDIO] {date}: dist={c.distance}, dur={c.duration}min, speed={speed:.2f}km/h, effort={effort:.2f}")
        elif c.distance:
            effort = c.distance * 10
            print(f"[CARDIO] {date}: distance-only fallback, effort={effort}")
        elif c.duration:
            effort = c.duration * 5
            print(f"[CARDIO] {date}: duration-only fallback, effort={effort}")
        else:
            effort = None
            print(f"[WARNING] {date}: Skipped cardio entry (no distance or duration)")

        data.append({
            "type": "cardio",
            "date": date,
            "duration_minutes": c.duration,
            "distance": c.distance,
            "effort": effort
        })

    data.sort(key=lambda x: x["date"])
    print(f"[INFO] Returning {len(data)} total entries for '{exercise_name}'")
    return jsonify(data)

