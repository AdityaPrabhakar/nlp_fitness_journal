from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import PersonalRecord
from init import db

personal_record_bp = Blueprint("personal_record_bp", __name__)

@personal_record_bp.route("/api/personal-records", methods=["GET"])
@jwt_required()
def get_personal_records():
    try:
        user_id = get_jwt_identity()

        records = (
            db.session.query(PersonalRecord)
            .filter(PersonalRecord.user_id == user_id)
            .order_by(PersonalRecord.exercise.asc(), PersonalRecord.field.asc())
            .all()
        )

        result = []
        for pr in records:
            result.append({
                "exercise": pr.exercise,
                "type": pr.type,
                "field": pr.field,
                "value": pr.value,
                "session_id": pr.session_id,
                "datetime": pr.datetime.format()
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
