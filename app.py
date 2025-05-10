# app.py
import os

from dotenv import load_dotenv
from init import create_app, db
from seed import seed_test_data

load_dotenv()

ENV = os.getenv("ENV", "production")

# Override config if testing
config_override = {}
if ENV == "testing":
    config_override["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"

app = create_app(config_override)

if ENV == "testing":
    with app.app_context():
        seed_test_data()

if __name__ == "__main__":
    app.run(debug=(ENV != "production"))
