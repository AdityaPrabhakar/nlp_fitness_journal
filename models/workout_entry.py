from init import db

class WorkoutEntry(db.Model):
    __tablename__ = "workout_entry"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('workout_session.id'), nullable=False)
    type = db.Column(db.String, nullable=False)
    exercise = db.Column(db.String, nullable=False)
    duration = db.Column(db.Float, nullable=True)
    distance = db.Column(db.Float, nullable=True)
    sets = db.Column(db.Integer, nullable=True)
    reps = db.Column(db.Integer, nullable=True)
    weight = db.Column(db.Float, nullable=True)

    @classmethod
    def from_dict(cls, data, session_id):
        return cls(
            session_id=session_id,
            type=data.get("type"),
            exercise=data.get("exercise"),
            duration=data.get("duration"),
            distance=data.get("distance"),
            sets=data.get("sets"),
            reps=data.get("reps"),
            weight=data.get("weight")
        )
