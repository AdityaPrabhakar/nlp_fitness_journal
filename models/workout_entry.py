from init import db

class WorkoutEntry(db.Model):
    __tablename__ = "workout_entry"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('workout_session.id'), nullable=False)
    type = db.Column(db.String, nullable=False)
    exercise = db.Column(db.String, nullable=False)
    notes = db.Column(db.Text, nullable=True)

    strength_entries = db.relationship('StrengthEntry', backref='entry', lazy=True)
    cardio_detail = db.relationship('CardioEntry', backref='entry', uselist=False)

    @staticmethod
    def from_dict(data, session_id):
        from models import StrengthEntry, CardioEntry
        entry = WorkoutEntry(
            session_id=session_id,
            type=data["type"],
            exercise=data["exercise"],
            notes=data.get("notes")
        )
        db.session.add(entry)
        db.session.flush()  # get entry.id

        if data["type"] == "strength":
            for i, s in enumerate(data.get("sets_details", []), start=1):
                strength_set = StrengthEntry(
                    entry_id=entry.id,
                    set_number=s.get("set_number", i),
                    reps=s.get("reps"),  # ← allow None
                    weight=s.get("weight")
                )
                db.session.add(strength_set)

        elif data["type"] == "cardio":
            cardio = CardioEntry(
                entry_id=entry.id,
                duration=data.get("duration"),
                distance=data.get("distance"),
                pace=data.get("pace")
            )
            db.session.add(cardio)

        return entry




