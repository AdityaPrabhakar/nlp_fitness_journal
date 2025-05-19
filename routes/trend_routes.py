from flask import Blueprint, jsonify
from collections import defaultdict
from init import db
from models import WorkoutSession, WorkoutEntry, StrengthEntry, CardioEntry

trend_bp = Blueprint('trend', __name__)

@trend_bp.route('/api/workout-trends/<int:session_id>', methods=['GET'])
def workout_trends(session_id):
    session = WorkoutSession.query.get(session_id)
    if not session:
        return jsonify({'error': 'Workout session not found'}), 404

    strength_result = []
    cardio_result = []

    for entry in session.entries:
        if entry.type == 'strength':
            # Current session sets
            strength_sets = StrengthEntry.query.filter_by(entry_id=entry.id).order_by(StrengthEntry.set_number).all()
            sets_data = [
                {
                    "set_number": s.set_number,
                    "reps": s.reps,
                    "weight": s.weight
                }
                for s in strength_sets
            ]

            # Historical sets grouped by session (date + notes)
            historical_sets = (
                db.session.query(
                    WorkoutSession.date,
                    WorkoutEntry.notes,
                    StrengthEntry.reps,
                    StrengthEntry.weight
                )
                .join(WorkoutEntry, WorkoutEntry.session_id == WorkoutSession.id)
                .join(StrengthEntry, StrengthEntry.entry_id == WorkoutEntry.id)
                .filter(
                    WorkoutEntry.exercise == entry.exercise,
                    WorkoutEntry.type == 'strength',
                    WorkoutSession.id != session_id
                )
                .order_by(WorkoutSession.date.asc())
                .all()
            )

            grouped_history = defaultdict(list)
            for date, notes, reps, weight in historical_sets:
                key = (date.format(), notes or "")
                grouped_history[key].append({
                    "reps": reps,
                    "weight": weight
                })

            history_data = [
                {
                    "date": date,
                    "notes": notes,
                    "sets": sets
                }
                for (date, notes), sets in grouped_history.items()
            ]

            strength_result.append({
                "exercise": entry.exercise,
                "notes": entry.notes or "",
                "sets": sets_data,
                "history": history_data
            })

        elif entry.type == 'cardio':
            cardio = CardioEntry.query.filter_by(entry_id=entry.id).first()
            if cardio:
                if cardio.distance and cardio.duration and cardio.distance != 0:
                    pace = round(cardio.duration / cardio.distance, 2)
                else:
                    pace = None

                historical_cardio = (
                    db.session.query(
                        WorkoutSession.date,
                        WorkoutEntry.notes,
                        CardioEntry.distance,
                        CardioEntry.duration
                    )
                    .join(WorkoutEntry, WorkoutEntry.session_id == WorkoutSession.id)
                    .join(CardioEntry, CardioEntry.entry_id == WorkoutEntry.id)
                    .filter(
                        WorkoutEntry.exercise == entry.exercise,
                        WorkoutEntry.type == 'cardio',
                        WorkoutSession.id != session_id
                    )
                    .order_by(WorkoutSession.date.asc())
                    .all()
                )

                grouped_history = {}
                for date, notes, distance, duration in historical_cardio:
                    key = (date.format(), notes or "")
                    grouped_history[key] = {
                        "distance": distance,
                        "duration": duration,
                        "pace": round(duration / distance, 2) if distance and duration else None
                    }

                cardio_history = [
                    {
                        "date": date,
                        "notes": notes,
                        **data
                    }
                    for (date, notes), data in grouped_history.items()
                ]

                cardio_result.append({
                    "activity": entry.exercise,
                    "notes": entry.notes or "",
                    "entry": {
                        "distance": cardio.distance,
                        "duration": cardio.duration,
                        "pace": pace
                    },
                    "history": cardio_history
                })

    return jsonify({
        "strength": strength_result,
        "cardio": cardio_result
    })
