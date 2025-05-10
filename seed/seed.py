import json
import os
from config import TestingConfig
from init import create_app, db
from models import WorkoutSession, WorkoutEntry
from dotenv import load_dotenv
from flask import current_app

# Load environment variables from .env file
load_dotenv()

def seed_test_data():
    # Get the path of the data file from the environment variable, with a fallback
    data_file_path = current_app.config.get("SEED_DATA_FILE_PATH")

    try:
        # Read data from the JSON file
        with open(data_file_path, 'r') as f:
            sample_sessions = json.load(f)
    except FileNotFoundError:
        print(f"Error: The data file '{data_file_path}' was not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: The data file '{data_file_path}' is not a valid JSON file.")
        return

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
                entry = WorkoutEntry.from_dict(entry_data, session.id)
                db.session.add(entry)

        db.session.commit()  # Commit all entries
        print("Test data seeded successfully.")
