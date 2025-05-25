from flask import Blueprint, jsonify, request, render_template
from collections import defaultdict

from flask_jwt_extended import jwt_required, get_jwt_identity

from init import db
from models import WorkoutSession, WorkoutEntry, StrengthEntry, CardioEntry
from datetime import datetime

trend_bp = Blueprint('trend', __name__)

@trend_bp.route("/api/strength-exercise-trends")
def strength_exercise_trends():
    return render_template("partials/strength_exercise_trends.html")

@trend_bp.route("/api/cardio-exercise-trends")
def cardio_exercise_trends():
    return render_template("partials/cardio_exercise_trends.html")

@trend_bp.route('/api/workout-trends/<int:session_id>', methods=['GET'])
@jwt_required()
def workout_trends(session_id):
    user_id = get_jwt_identity()

    session = WorkoutSession.query.filter_by(id=session_id, user_id=user_id).first()
    if not session:
        return jsonify({'error': 'Workout session not found'}), 404

    date_param = request.args.get('date')
    count_param = request.args.get('count', type=int)

    try:
        filter_date = datetime.strptime(date_param, '%Y-%m-%d').date() if date_param else None
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

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

            # Historical strength sets including set_number
            historical_query = (
                db.session.query(
                    WorkoutSession.date,
                    WorkoutEntry.notes,
                    StrengthEntry.set_number,
                    StrengthEntry.reps,
                    StrengthEntry.weight
                )
                .join(WorkoutEntry, WorkoutEntry.session_id == WorkoutSession.id)
                .join(StrengthEntry, StrengthEntry.entry_id == WorkoutEntry.id)
                .filter(
                    WorkoutEntry.exercise == entry.exercise,
                    WorkoutEntry.type == 'strength',
                    WorkoutSession.user_id == user_id,
                    WorkoutSession.id != session_id
                )
            )

            if filter_date:
                historical_query = historical_query.filter(
                    (WorkoutSession.date < filter_date) |
                    ((WorkoutSession.date == filter_date) & (WorkoutSession.id < session_id))
                )

            historical_query = historical_query.order_by(WorkoutSession.date.desc())
            if count_param:
                historical_query = historical_query.limit(count_param)

            historical_sets = historical_query.all()

            grouped_history = defaultdict(list)
            for date, notes, set_number, reps, weight in historical_sets:
                key = (date.format(), notes or "")
                grouped_history[key].append({
                    "set_number": set_number,
                    "reps": reps,
                    "weight": weight
                })

            # Sort each set list by set_number
            history_data = [
                {
                    "date": date,
                    "notes": notes,
                    "sets": sorted(sets, key=lambda s: s["set_number"])
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
                        WorkoutSession.user_id == user_id,
                        WorkoutSession.id != session_id
                    )
                )

                if filter_date:
                    historical_query = historical_query.filter(
                        (WorkoutSession.date < filter_date) |
                        ((WorkoutSession.date == filter_date) & (WorkoutSession.id < session_id))
                    )

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
        "session_date": session.date.format(),
        "strength": strength_result,
        "cardio": cardio_result
    })