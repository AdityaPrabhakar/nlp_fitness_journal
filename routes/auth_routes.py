from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import User
from init import db
import re

auth_bp = Blueprint('auth', __name__, template_folder='templates')
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Serve login page
@auth_bp.route('/auth/login', methods=['GET'])
def login_page():
    return render_template('partials/login.html')

# Login API
@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password."}), 401

    access_token = create_access_token(identity=str(user.id))
    return jsonify(access_token=access_token, display_name=user.display_name or user.email), 200

# Serve signup page
@auth_bp.route('/auth/signup', methods=['GET'])
def signup_page():
    return render_template('partials/signup.html')

# Signup API
@auth_bp.route('/api/auth/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()
    display_name = data.get('display_name', '').strip()

    if not email or not password or not display_name:
        return jsonify({"error": "Email, display name, and password are required."}), 400

    if not EMAIL_REGEX.match(email):
        return jsonify({"error": "Invalid email address."}), 400

    if len(display_name) < 3:
        return jsonify({"error": "Display name must be at least 3 characters."}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with that email already exists."}), 409

    new_user = User(email=email, display_name=display_name)
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    access_token = create_access_token(identity=str(new_user.id))
    return jsonify(access_token=access_token, display_name=new_user.display_name), 201

# Optional logout
@auth_bp.route('/logout')
def logout():
    return redirect(url_for('auth.login_page'))

@auth_bp.route('/api/auth/update-physique', methods=['POST'])
@jwt_required()
def update_physique():
    data = request.get_json()
    user_id = get_jwt_identity()

    bodyweight = data.get('bodyweight')
    height = data.get('height')

    if bodyweight is None and height is None:
        return jsonify({"error": "At least one of bodyweight or height must be provided."}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404

    if bodyweight is not None:
        try:
            user.bodyweight = float(bodyweight)
        except ValueError:
            return jsonify({"error": "Invalid bodyweight format."}), 400

    if height is not None:
        try:
            user.height = float(height)
        except ValueError:
            return jsonify({"error": "Invalid height format."}), 400

    db.session.commit()
    return jsonify({
        "message": "Physique updated.",
        "bodyweight": user.bodyweight,
        "height": user.height
    }), 200
