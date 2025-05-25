from init import db
from datetime import datetime

class PersonalRecord(db.Model):
    __tablename__ = "personal_records"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    exercise = db.Column(db.String, nullable=False)
    type = db.Column(db.String, nullable=False)  # "strength" or "cardio"
    field = db.Column(db.String, nullable=False)  # "weight", "reps", "volume", "distance", "duration", "pace"
    value = db.Column(db.Float, nullable=False)
    units = db.Column(db.String, nullable=False)  # New field for units like "lbs", "reps", "mi", "min", "min/mi"

    session_id = db.Column(db.Integer, db.ForeignKey("workout_session.id"), nullable=False)
    datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", backref="personal_records")
