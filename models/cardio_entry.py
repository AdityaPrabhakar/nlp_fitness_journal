from init import db

class CardioEntry(db.Model):
    __tablename__ = "cardio_entry"

    id = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, db.ForeignKey('workout_entry.id'), nullable=False)
    duration = db.Column(db.Float, nullable=True)  # in minutes
    distance = db.Column(db.Float, nullable=True)  # in miles
    pace = db.Column(db.Float, nullable=True)      # in minutes per mile
