from flask import Blueprint, jsonify
from models import PersonalRecord, WorkoutSession
from init import db

personal_record_bp = Blueprint("personal_record_bp", __name__)

@personal_record_bp.route("/api/personal-records", methods=["GET"])
def get_personal_records():

    try:
        records = (
            db.session.query(PersonalRecord, WorkoutSession.date)
            .join(WorkoutSession, WorkoutSession.id == PersonalRecord.session_id)
            .order_by(PersonalRecord.exercise.asc(), PersonalRecord.field.asc())
            .all()
        )

        result = []
        for pr, session_date in records:
            result.append({
                "exercise": pr.exercise,
                "type": pr.type,
                "field": pr.field,
                "value": pr.value,
                "session_id": pr.session_id,
                "date": session_date.isoformat()
            })

        return jsonify({
            "success": True,
            "personal_records": result
        }), 200

    except Exception as e:
        print("Error fetching personal records:", e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
