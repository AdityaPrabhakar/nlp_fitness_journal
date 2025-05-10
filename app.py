# app.py
import os
from dotenv import load_dotenv
from init import create_app
from seed import seed_test_data
from config import CONFIG_MAP

load_dotenv()

env = os.getenv("ENV", "standard").lower()
config_class = CONFIG_MAP.get(env)

if not config_class:
    raise ValueError(f"Unknown ENV '{env}' in .env")

app = create_app(config_class)

if env == "testing":
    with app.app_context():
        seed_test_data()

if __name__ == "__main__":
    app.run(debug=app.config.get("DEBUG", False))
