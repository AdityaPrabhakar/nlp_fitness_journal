# models.py
from flask_sqlalchemy import SQLAlchemy
from init import db

class WorkoutSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String, nullable=False)
    raw_text = db.Column(db.Text, nullable=False)
    entries = db.relationship('WorkoutEntry', backref='session', lazy=True)

class WorkoutEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('workout_session.id'), nullable=False)
    type = db.Column(db.String, nullable=False)
    exercise = db.Column(db.String, nullable=False)
    duration = db.Column(db.Float, nullable=True)
    distance = db.Column(db.Float, nullable=True)
    sets = db.Column(db.Integer, nullable=True)
    reps = db.Column(db.Integer, nullable=True)
    weight = db.Column(db.Float, nullable=True)

