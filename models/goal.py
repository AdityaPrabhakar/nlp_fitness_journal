from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, Boolean,
    ForeignKey, Enum, Text
)
from sqlalchemy.orm import relationship

import enum

from init import db


# Enums for metrics and exercise types
class ExerciseTypeEnum(enum.Enum):
    strength = 'strength'
    cardio = 'cardio'
    general = 'general'  # For generic/non-exercise-specific goals

class MetricEnum(enum.Enum):
    reps = 'reps'
    sets = 'sets'
    distance = 'distance'
    duration = 'duration'
    weight = 'weight'
    sessions = 'sessions'
    pace = 'pace'

class RepeatIntervalEnum(enum.Enum):
    daily = 'daily'
    weekly = 'weekly'
    monthly = 'monthly'
    yearly = 'yearly'

class GoalTypeEnum(enum.Enum):
    single_session = 'single_session'
    aggregate = 'aggregate'
    # These are reserved for expansion later
    # streak = 'streak'
    # progress = 'progress'
    # pr = 'pr'
    # compound = 'compound'

class Goal(db.Model):
    __tablename__ = 'goals'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)

    name = Column(String, nullable=False)
    description = Column(Text)

    start_date = Column(Date, nullable=False)
    end_date = Column(Date)

    goal_type = Column(Enum(GoalTypeEnum), nullable=False)
    is_repeatable = Column(Boolean, default=False)
    repeat_interval = Column(Enum(RepeatIntervalEnum), nullable=True)

    exercise_type = Column(Enum(ExerciseTypeEnum), nullable=True)
    exercise_name = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    targets = relationship("GoalTarget", back_populates="goal", cascade="all, delete-orphan")
    progress = relationship("GoalProgress", back_populates="goal", cascade="all, delete-orphan")


class GoalTarget(db.Model):
    __tablename__ = 'goal_targets'

    id = Column(Integer, primary_key=True)
    goal_id = Column(Integer, ForeignKey('goals.id'), nullable=False)

    metric = Column(Enum(MetricEnum), nullable=False)
    value = Column(Float, nullable=False)

    goal = relationship("Goal", back_populates="targets")


class GoalProgress(db.Model):
    __tablename__ = 'goal_progress'

    id = Column(Integer, primary_key=True)
    goal_id = Column(Integer, ForeignKey('goals.id'), nullable=False)
    session_id = Column(Integer, ForeignKey('workout_session.id'))

    value_achieved = Column(Float, nullable=False)
    achieved_on = Column(Date, nullable=False, default=datetime.utcnow)

    goal = relationship("Goal", back_populates="progress")
