# config.py
import os
from datetime import timedelta

class BaseConfig:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    SEED_DATA_FILE_PATH = os.getenv("SEED_DATA_FILE_PATH", "sample_sessions.json")
    SECRET_KEY = os.getenv("SECRET_KEY")

    # Default JWT token expiration: 1 day
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)

class StandardConfig(BaseConfig):
    DEBUG = True
    if os.getenv("FLASK_ENV") == "production":
        SQLALCHEMY_DATABASE_URI = os.getenv("STANDARD_DATABASE_URL")
    else:
        SQLALCHEMY_DATABASE_URI = "sqlite:///database.db"


class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite:///test.db")

# Optional helper for lookup
CONFIG_MAP = {
    "standard": StandardConfig,
    "testing": TestingConfig,
}
