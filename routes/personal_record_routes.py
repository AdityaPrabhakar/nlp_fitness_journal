from datetime import datetime
from collections import defaultdict

from flask import Blueprint, jsonify, request
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
                "units": pr.units,
                "session_id": pr.session_id,
                "datetime": pr.datetime.isoformat()
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


@personal_record_bp.route("/api/personal-records/by-exercise/<string:exercise>", methods=["GET"])
@jwt_required()
def get_personal_records_by_exercise(exercise):
    try:
        user_id = get_jwt_identity()
        start_date_str = request.args.get("start_date")
        end_date_str = request.args.get("end_date")

        if not exercise:
            return jsonify({"success": False, "error": "Exercise name is required."}), 400

        query = db.session.query(PersonalRecord).filter(
            PersonalRecord.user_id == user_id,
            PersonalRecord.exercise.ilike(exercise)
        )

        if start_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str)
                query = query.filter(PersonalRecord.datetime >= start_date)
            except ValueError:
                return jsonify({"success": False, "error": "Invalid start_date format. Use YYYY-MM-DD."}), 400

        if end_date_str:
            try:
                end_date = datetime.fromisoformat(end_date_str)
                query = query.filter(PersonalRecord.datetime <= end_date)
            except ValueError:
                return jsonify({"success": False, "error": "Invalid end_date format. Use YYYY-MM-DD."}), 400

        records = query.order_by(PersonalRecord.field.asc(), PersonalRecord.datetime.desc()).all()

        pr_by_field = defaultdict(list)
        for pr in records:
            pr_by_field[pr.field].append(pr)

        result = []
        for field, prs in pr_by_field.items():
            latest_pr = max(prs, key=lambda pr: pr.datetime)  # <-- changed here
            for pr in prs:
                result.append({
                    "exercise": pr.exercise,
                    "type": pr.type,
                    "field": pr.field,
                    "value": pr.value,
                    "units": pr.units,
                    "session_id": pr.session_id,
                    "datetime": pr.datetime.isoformat(),
                    "is_latest": pr.id == latest_pr.id
                })

        return jsonify({
            "success": True,
            "exercise": exercise,
            "personal_records": result
        }), 200

    except Exception as e:
        print("Error fetching personal records by exercise:", e)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500