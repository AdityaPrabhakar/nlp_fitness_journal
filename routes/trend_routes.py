from flask import Blueprint, jsonify, request
from collections import defaultdict
from init import db
from models import WorkoutSession, WorkoutEntry, StrengthEntry, CardioEntry
from datetime import datetime

trend_bp = Blueprint('trend', __name__)

@trend_bp.route('/api/workout-trends/<int:session_id>', methods=['GET'])
def workout_trends(session_id):
    session = WorkoutSession.query.get(session_id)
    if not session:
        return jsonify({'error': 'Workout session not found'}), 404

    # Get query parameters
    date_param = request.args.get('date')  # e.g., '2025-05-01'
    count_param = request.args.get('count', type=int)  # default: None

    try:
        if date_param:
            filter_date = datetime.strptime(date_param, '%Y-%m-%d').date()
        else:
            filter_date = None
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    strength_result = []
    cardio_result = []

    for entry in session.entries:
        if entry.type == 'strength':
            strength_sets = StrengthEntry.query.filter_by(entry_id=entry.id).order_by(StrengthEntry.set_number).all()
            sets_data = [
                {
                    "set_number": s.set_number,
                    "reps": s.reps,
                    "weight": s.weight
                }
                for s in strength_sets
            ]

            historical_query = (
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
            )

            if filter_date:
                historical_query = historical_query.filter(WorkoutSession.date < filter_date)

            historical_query = historical_query.order_by(WorkoutSession.date.desc())

            if count_param:
                historical_query = historical_query.limit(count_param)

            historical_sets = historical_query.all()

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
                pace = round(cardio.duration / cardio.distance, 2) if cardio.distance and cardio.duration and cardio.distance != 0 else None

                historical_query = (
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
                )

                if filter_date:
                    historical_query = historical_query.filter(WorkoutSession.date < filter_date)

                historical_query = historical_query.order_by(WorkoutSession.date.desc())

                if count_param:
                    historical_query = historical_query.limit(count_param)

                historical_cardio = historical_query.all()

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
        "session_date": session.date.format(),  # <-- add this line
        "strength": strength_result,
        "cardio": cardio_result
    })

