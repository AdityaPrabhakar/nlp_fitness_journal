from init import db
from datetime import time

class WorkoutSession(db.Model):
    __tablename__ = "workout_session"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    date = db.Column(db.String, nullable=False)  # Consider changing this to db.Date if you're using proper dates
    time = db.Column(db.Time, nullable=True)     # <-- NEW time field

    raw_text = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text, nullable=True)

    entries = db.relationship('WorkoutEntry', backref='session', lazy=True)
    user = db.relationship('User', backref='workout_sessions')

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "date": self.date,
            "time": self.time.strftime("%H:%M:%S") if self.time else None,  # Add time to output
            "raw_text": self.raw_text,
            "notes": self.notes,
            "entries": [entry.to_dict() for entry in self.entries]
        }
