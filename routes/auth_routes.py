from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_jwt_extended import create_access_token
from werkzeug.security import check_password_hash, generate_password_hash
from models import User
from init import db

auth_bp = Blueprint('auth', __name__, template_folder='templates')

# Serve login page
@auth_bp.route('/auth/login', methods=['GET'])
def login_page():
    return render_template('partials/login.html')

# API: login POST
@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid username or password"}), 401

    access_token = create_access_token(identity=str(user.id))
    return jsonify(access_token=access_token, username=user.username), 200

# Serve signup page
@auth_bp.route('/auth/signup', methods=['GET'])
def signup_page():
    return render_template('partials/signup.html')

# API: signup POST
@auth_bp.route('/api/auth/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"error": "Username already exists"}), 409

    new_user = User(
        username=username,
        password_hash=generate_password_hash(password)
    )
    db.session.add(new_user)
    db.session.commit()

    access_token = create_access_token(identity=str(new_user.id))
    return jsonify(access_token=access_token, username=new_user.username), 201

# Add this logout route (optional server redirect)
@auth_bp.route('/logout')
def logout():
    return redirect(url_for('auth.login_page'))
