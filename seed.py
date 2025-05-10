from models import WorkoutSession, WorkoutEntry
from datetime import datetime

def seed_test_data(db):
    print("Seeding test data...")

    # Clear existing data
    db.session.query(WorkoutEntry).delete()
    db.session.query(WorkoutSession).delete()
    db.session.commit()

    sample_sessions = [
        # (date, raw_text, entries)
        ("2025-05-01", "Ran 3 miles in 30 minutes, did 3 sets of 10 pushups.", [
            {"type": "cardio", "exercise": "running", "distance": 3.0, "duration": 30},
            {"type": "strength", "exercise": "pushups", "sets": 3, "reps": 10},
        ]),
        ("2025-05-02", "Cycled 15 miles in 45 minutes, did 4 sets of 12 squats.", [
            {"type": "cardio", "exercise": "cycling", "distance": 15.0, "duration": 45},
            {"type": "strength", "exercise": "squats", "sets": 4, "reps": 12},
        ]),
        ("2025-05-03", "5 miles running in 50 minutes, 3 sets of 8 pullups.", [
            {"type": "cardio", "exercise": "running", "distance": 5.0, "duration": 50},
            {"type": "strength", "exercise": "pullups", "sets": 3, "reps": 8},
        ]),
        ("2025-05-04", "Jump rope for 20 minutes, 5 sets of 5 deadlifts.", [
            {"type": "cardio", "exercise": "jump rope", "duration": 20},
            {"type": "strength", "exercise": "deadlifts", "sets": 5, "reps": 5},
        ]),
        ("2025-05-05", "Swam for 40 minutes and ran 2 miles.", [
            {"type": "cardio", "exercise": "swimming", "duration": 40},
            {"type": "cardio", "exercise": "running", "distance": 2.0}
        ])
    ]

    for date, raw_text, entries in sample_sessions:
        session = WorkoutSession(date=date, raw_text=raw_text)
        db.session.add(session)
        db.session.commit()  # Commit to get session ID

        for e in entries:
            entry = WorkoutEntry(
                session_id=session.id,
                type=e["type"],
                exercise=e["exercise"],
                duration=e.get("duration"),
                distance=e.get("distance"),
                sets=e.get("sets"),
                reps=e.get("reps")
            )
            db.session.add(entry)

    db.session.commit()
    print("Test data seeded successfully.")
