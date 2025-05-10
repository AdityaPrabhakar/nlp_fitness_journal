# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app(config_override=None):
    app = Flask(__name__)

    # Default config (used in production or overridden)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Apply external overrides (e.g., from app.py or tests)
    if config_override:
        app.config.update(config_override)

    db.init_app(app)

    with app.app_context():
        import models
        import routes
        db.create_all()

    return app
