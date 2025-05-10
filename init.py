from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

db = SQLAlchemy()

def create_app():
    load_dotenv()
    ENV = os.getenv("ENV", "production")

    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "sqlite:///test.db" if ENV == "testing" else "sqlite:///database.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        import models
        import routes
        db.create_all()
        if ENV == "testing":
            from seed import seed_test_data
            seed_test_data(db)

    return app
