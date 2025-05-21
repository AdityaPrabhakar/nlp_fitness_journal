# init.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS


db = SQLAlchemy()
jwt = JWTManager()  # Step 1: Create the JWTManager instance

def create_app(config_class):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app, supports_credentials=True, expose_headers=["Authorization"])

    db.init_app(app)
    jwt.init_app(app)  # Step 2: Initialize JWTManager with app

    with app.app_context():
        db.create_all()

    return app
