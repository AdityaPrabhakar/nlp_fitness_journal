from datetime import datetime

from flask import request, jsonify

from models import WorkoutSession


def estimate_1rm(reps, weight, formula="epley"):
    if reps <= 0 or weight <= 0:
        return None

    formula = formula.lower()

    if formula == "epley":
        return weight * (1 + reps / 30)
    elif formula == "brzycki":
        return weight * (36 / (37 - reps))
    elif formula == "lombardi":
        return weight * (reps ** 0.10)
    elif formula == "mayhew":
        return (100 * weight) / (52.2 + 41.9 * (2.71828 ** (-0.055 * reps)))
    elif formula == "oconner":
        return weight * (1 + 0.025 * reps)
    else:
        # Default fallback to Epley if unknown
        return weight * (1 + reps / 30)

def apply_date_filters(query):
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    if start_date:
        try:
            start_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            query = query.filter(WorkoutSession.date >= start_obj)
        except ValueError:
            return None, jsonify({"error": "Invalid start_date format"}), 400

    if end_date:
        try:
            end_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
            query = query.filter(WorkoutSession.date <= end_obj)
        except ValueError:
            return None, jsonify({"error": "Invalid end_date format"}), 400

    return query, None, None
