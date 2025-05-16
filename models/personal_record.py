from init import db

class PersonalRecord(db.Model):
    __tablename__ = "personal_records"

    id = db.Column(db.Integer, primary_key=True)
    exercise = db.Column(db.String, nullable=False)
    type = db.Column(db.String, nullable=False)  # "strength" or "cardio"
    field = db.Column(db.String, nullable=False)  # "weight", "reps", "volume", "distance", "duration"
    value = db.Column(db.Float, nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey("workout_session.id"), nullable=False)
