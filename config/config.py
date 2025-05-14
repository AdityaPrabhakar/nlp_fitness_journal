# config.py
import os

class BaseConfig:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    SEED_DATA_FILE_PATH = os.getenv("SEED_DATA_FILE_PATH", "sample_sessions.json")
    SECRET_KEY = os.getenv("SECRET_KEY")

class StandardConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv("STANDARD_DATABASE_URL", "sqlite:///database.db")

class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite:///test.db")

# Optional helper for lookup
CONFIG_MAP = {
    "standard": StandardConfig,
    "testing": TestingConfig,
}
