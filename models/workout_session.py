from init import db

class WorkoutSession(db.Model):
    __tablename__ = "workout_session"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    date = db.Column(db.String, nullable=False)
    raw_text = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text, nullable=True)

    entries = db.relationship('WorkoutEntry', backref='session', lazy=True)
    user = db.relationship('User', backref='workout_sessions')

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "date": self.date,
            "raw_text": self.raw_text,
            "notes": self.notes,
            "entries": [entry.to_dict() for entry in self.entries]  # requires WorkoutEntry.to_dict()
        }

