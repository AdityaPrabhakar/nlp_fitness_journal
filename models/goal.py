from init import db
from datetime import datetime


class Goal(db.Model):
    __tablename__ = "goal"

    id = db.Column(db.Integer, primary_key=True)
    exercise = db.Column(db.String, nullable=False)  # Exercise the goal applies to
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String, nullable=False, default='ongoing')  # 'ongoing', 'completed', 'expired'

    # Relationship to GoalTarget to track multiple targets for this goal
    targets = db.relationship('GoalTarget', backref='goal', lazy=True)

    @staticmethod
    def from_dict(data):
        goal = Goal(
            exercise=data["exercise"],
            start_date=data["start_date"],
            end_date=data["end_date"],
            status=data.get("status", "ongoing")
        )
        # Add goal targets from data
        for target_data in data["targets"]:
            goal_target = GoalTarget.from_dict(target_data, goal.id)
            goal.targets.append(goal_target)
        return goal

    def __repr__(self):
        return f"<Goal {self.exercise} from {self.start_date} to {self.end_date}>"


class GoalTarget(db.Model):
    __tablename__ = "goal_target"

    id = db.Column(db.Integer, primary_key=True)
    goal_id = db.Column(db.Integer, db.ForeignKey('goal.id'), nullable=False)  # Foreign key to Goal
    target_field = db.Column(db.String,
                             nullable=False)  # Field to track (e.g., 'sets', 'reps', 'distance', 'duration', etc.)
    target_value = db.Column(db.Float, nullable=False)  # The target value for this field (e.g., 100 miles, 50 sets)

    @staticmethod
    def from_dict(data, goal_id):
        return GoalTarget(
            goal_id=goal_id,
            target_field=data["target_field"],
            target_value=data["target_value"]
        )

    def __repr__(self):
        return f"<GoalTarget {self.target_field}: {self.target_value}>"
