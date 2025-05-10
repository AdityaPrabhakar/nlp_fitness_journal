from init import db

class WorkoutSession(db.Model):
    __tablename__ = "workout_session"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String, nullable=False)
    raw_text = db.Column(db.Text, nullable=False)
    entries = db.relationship('WorkoutEntry', backref='session', lazy=True)
