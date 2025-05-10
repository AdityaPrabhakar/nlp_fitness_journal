from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class WorkoutEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    structured_data = db.Column(db.Text)
