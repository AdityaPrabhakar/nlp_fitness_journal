# seed.py
import json

from config import TestingConfig
from init import create_app, db
from models import WorkoutSession, WorkoutEntry


def seed_test_data():
    # Read data from the JSON file
    with open('sample_sessions.json', 'r') as f:
        sample_sessions = json.load(f)

    # Create Flask app context for this seeding operation
    app = create_app(TestingConfig)

    with app.app_context():
        print("Dropping and creating the schema...")
        db.drop_all()  # Drop all tables (to avoid duplicates)
        db.create_all()  # Recreate schema

        print("Seeding test data...")

        # Iterate through sample_sessions and add them to the DB
        for session_data in sample_sessions:
            session = WorkoutSession(date=session_data["date"], raw_text=session_data["raw_text"])
            db.session.add(session)
            db.session.commit()  # Commit to get session ID

            # Add entries to the session
            for entry_data in session_data["entries"]:
                entry = WorkoutEntry(
                    session_id=session.id,
                    type=entry_data["type"],
                    exercise=entry_data["exercise"],
                    duration=entry_data.get("duration"),
                    distance=entry_data.get("distance"),
                    sets=entry_data.get("sets"),
                    reps=entry_data.get("reps"),
                    weight=entry_data.get("weight")
                )
                db.session.add(entry)

        db.session.commit()  # Commit all entries
        print("Test data seeded successfully.")
