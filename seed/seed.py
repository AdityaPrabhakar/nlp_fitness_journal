import json
from config import TestingConfig
from init import create_app, db
from models import User, WorkoutSession, WorkoutEntry, StrengthEntry, CardioEntry
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
from flask import current_app

# Load environment variables from .env file
load_dotenv()

def calculate_pace(duration_minutes, distance):
    if duration_minutes and distance and distance > 0:
        return round(duration_minutes / distance, 2)
    return None

def seed_test_data():
    app = create_app(TestingConfig)

    with app.app_context():
        # Get the path of the data file from the environment variable
        data_file_path = current_app.config.get("SEED_DATA_FILE_PATH")

        try:
            with open(data_file_path, 'r') as f:
                sample_sessions = json.load(f)
        except FileNotFoundError:
            print(f"Error: The data file '{data_file_path}' was not found.")
            return
        except json.JSONDecodeError:
            print(f"Error: The data file '{data_file_path}' is not a valid JSON file.")
            return

        print("Dropping and creating the schema...")
        db.drop_all()
        db.create_all()

        print("Seeding test user...")
        test_user = User(
            id=1,
            email="sampleuser@example.com",
            display_name="SampleUser",
            password_hash=generate_password_hash("Password123!"),
            bodyweight=180.0,
            height=70.0
        )
        db.session.add(test_user)
        db.session.commit()

        print("Seeding workout session data...")
        TEST_USER_ID = 1

        for session_data in sample_sessions:
            session = WorkoutSession(
                user_id=TEST_USER_ID,
                date=session_data["date"],
                raw_text=session_data["raw_text"],
                notes=session_data.get("notes")
            )
            db.session.add(session)
            db.session.commit()  # Save to generate session.id

            for entry_data in session_data["entries"]:
                entry = WorkoutEntry(
                    session_id=session.id,
                    type=entry_data["type"],
                    exercise=entry_data["exercise"],
                    notes=entry_data.get("notes")
                )
                db.session.add(entry)
                db.session.commit()  # Save to generate entry.id

                if entry.type == "strength":
                    for set_data in entry_data.get("strength_entries", []):
                        strength_set = StrengthEntry(
                            entry_id=entry.id,
                            set_number=set_data["set_number"],
                            reps=set_data["reps"],
                            weight=set_data.get("weight")
                        )
                        db.session.add(strength_set)

                elif entry.type == "cardio":
                    cardio_detail = entry_data.get("cardio_detail", {})
                    duration = cardio_detail.get("duration")  # in minutes
                    distance = cardio_detail.get("distance")  # in miles/km
                    pace = cardio_detail.get("pace")  # Optional, fallback to calculated
                    if pace is None:
                        pace = calculate_pace(duration, distance)

                    cardio = CardioEntry(
                        entry_id=entry.id,
                        duration=duration,
                        distance=distance,
                        pace=pace
                    )
                    db.session.add(cardio)

        db.session.commit()
        print("Test data seeded successfully.")
