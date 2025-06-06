from werkzeug.security import generate_password_hash, check_password_hash
from init import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    display_name = db.Column(db.String(80))  # Public-facing name
    password_hash = db.Column(db.String(512), nullable=False)  # ✅ increased size

    # American units
    bodyweight = db.Column(db.Float, nullable=True)  # In pounds (lbs)
    height = db.Column(db.Float, nullable=True)      # In inches (in)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
