# app.py
import os
from dotenv import load_dotenv

load_dotenv()

from init import create_app
from routes import register_routes
from seed.seed import seed_test_data
from config import CONFIG_MAP


env = os.getenv("ENV", "standard").lower()
config_class = CONFIG_MAP.get(env)

if not config_class:
    raise ValueError(f"Unknown ENV '{env}' in .env")

app = create_app(config_class)
register_routes(app)

if env == "testing":
    with app.app_context():
        seed_test_data()

if __name__ == "__main__":
    app.run(debug=app.config.get("DEBUG", False))
