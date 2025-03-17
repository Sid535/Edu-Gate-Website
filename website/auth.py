from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
import bcrypt
import uuid
import os
import re
import smtplib
from email.mime.text import MIMEText
from datetime import timedelta, datetime
from .models import db, User, PasswordReset
from .models import User, PasswordReset
from .database import db

auth = Blueprint('auth', __name__)

# Validation functions
def validate_name(name):
    return bool(re.match(r'^[a-zA-Z\s]+$', name))

def validate_username(username):
    return bool(re.match(r'^[a-zA-Z0-9_]+$', username))

def validate_email(email):
    return bool(re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email))

def validate_password(password):
    return len(password) >= 6

# Login page
@auth.route('/')
@auth.route('/login', methods=['GET'])
def login_page():
    if current_user.is_authenticated:
        next_page = request.args.get('next', '/home')
        return redirect(next_page)
    return render_template('login.html')

# Handle login API request
@auth.route('/api/login', methods=['POST'])
def login_api():
    data = request.get_json()
    
    if not data or ('email' not in data and 'username' not in data) or 'password' not in data:
        return jsonify({"message": "Missing login credentials or password"}), 400
    
    # Get either email or username
    identifier = data.get('email') or data.get('username')
    password = data['password']
    
    try:
        # Query for user by email or username
        user = User.query.filter((User.email == identifier) | (User.username == identifier)).first()
        
        if not user:
            return jsonify({"message": "Invalid credentials"}), 401

        # Verify password
        if user.check_password(password):
            # Login user
            login_user(user, remember=True)
            
            # Set session duration
            session.permanent = True

            return jsonify({"message": "Login successful"}), 200
        else:
            return jsonify({"message": "Invalid credentials"}), 401
            
    except Exception as e:
        return jsonify({"message": f"Error during login: {str(e)}"}), 500

# Registration page
@auth.route('/signup')
def signup_page():
    return render_template('signup.html')

# Handle registration API
@auth.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data or 'name' not in data or 'email' not in data or 'password' not in data or 'username' not in data:
        return jsonify({"message": "Missing required fields"}), 400

    name = data['name']
    email = data['email']
    username = data['username']
    password = data['password']
    
    # Server-side validation
    if not validate_name(name):
        return jsonify({"message": "Name should only contain letters and spaces"}), 400
    
    if not validate_username(username):
        return jsonify({"message": "Username should only contain letters, numbers, and underscores"}), 400
    
    if not validate_email(email):
        return jsonify({"message": "Please enter a valid email address"}), 400
    
    if not validate_password(password):
        return jsonify({"message": "Password must be at least 6 characters long"}), 400

    try:
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            return jsonify({"message": "Email already registered"}), 409
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            return jsonify({"message": "Username already taken"}), 409

        # Create new user with hashed password
        hashed_password = User.hash_password(password)
        new_user = User(name=name, email=email, username=username)
        new_user.password = hashed_password
        
        # Add and commit to database
        db.session.add(new_user)
        db.session.commit()
        
        # Log the user in
        login_user(new_user, remember=True)

        return jsonify({"message": "Registration successful"}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Registration error: {str(e)}"}), 500

# Forgot Password page
@auth.route('/forgot-password')
def forgot_password_page():
    return render_template('forgot-password.html')

# Handle forgot password request
@auth.route('/api/forgot-password', methods=['POST'])
def forgot_password_api():
    data = request.get_json()
    
    if not data or 'email' not in data:
        return jsonify({"message": "Email is required"}), 400
    
    email = data['email']
    
    try:
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Don't reveal if email exists or not for security
            return jsonify({"message": "If your email exists in our system, you will receive a password reset link"}), 200
        
        # Generate a reset token
        reset_token = str(uuid.uuid4())
        expiry = datetime.now() + timedelta(hours=24)
        
        # Check if a reset token already exists for this user
        existing_reset = PasswordReset.query.filter_by(user_id=user.id).first()
        
        if existing_reset:
            # Update existing token
            existing_reset.token = reset_token
            existing_reset.expires_at = expiry
        else:
            # Create new token
            new_reset = PasswordReset(user_id=user.id, token=reset_token, expires_at=expiry)
            db.session.add(new_reset)
        
        db.session.commit()
        
        # Create a reset link
        reset_link = f"{request.host_url}reset-password/{reset_token}"
        
        # Send email with reset link
        send_password_reset_email(email, reset_link, user.name)
        
        return jsonify({"message": "If your email exists in our system, you will receive a password reset link"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error processing request: {str(e)}"}), 500

# Function to send password reset email
def send_password_reset_email(email, reset_link, name):
    try:
        # Get email configuration from environment variables
        smtp_server = os.environ.get('SMTP_SERVER')
        smtp_port = os.environ.get('SMTP_PORT')
        smtp_username = os.environ.get('SMTP_USERNAME')
        smtp_password = os.environ.get('SMTP_PASSWORD')
        sender_email = os.environ.get('SENDER_EMAIL', 'noreply@yourdomain.com')
        
        print(f"Email config - Server: {'set' if smtp_server else 'not set'}, Port: {'set' if smtp_port else 'not set'}")  # debugging line
        
        # For development/testing: print the link instead of sending email
        print(f"===== PASSWORD RESET LINK =====")
        print(f"For user: {name} ({email})")
        print(f"Link: {reset_link}")
        print(f"===============================")
            
        # Create email message
        subject = "Password Reset Request"
        body = f"""Hello {name},

You recently requested to reset your password. Please click the link below to reset it:

{reset_link}

This link will expire in 24 hours.

If you did not request a password reset, please ignore this email or contact support if you have concerns.

Regards,
EduGate Team
"""
        
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = email
        
        # Send email
        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.starttls()  # Secure the connection
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        # Log this error, but don't expose to user

@auth.route('/reset-password/<token>', methods=['GET'])
def reset_password_page(token):
    return render_template('reset-password.html', token=token)

# Handle password reset
@auth.route('/api/reset-password', methods=['POST'])
def reset_password_api():
    data = request.get_json()
    
    if not data or 'token' not in data or 'password' not in data:
        return jsonify({"message": "Token and password are required"}), 400
    
    token = data['token']
    password = data['password']
    
    if not validate_password(password):
        return jsonify({"message": "Password must be at least 6 characters long"}), 400
    
    try:
        # Find valid reset token
        now = datetime.now()
        reset_request = PasswordReset.query.filter_by(token=token).filter(PasswordReset.expires_at > now).first()
        
        if not reset_request:
            return jsonify({"message": "Invalid or expired token"}), 400
        
        # Get user and update password
        user = User.query.get(reset_request.user_id)
        if not user:
            return jsonify({"message": "User not found"}), 404
            
        # Update password
        user.password = User.hash_password(password)
        
        # Delete the used token
        db.session.delete(reset_request)
        db.session.commit()
        
        return jsonify({"message": "Password successfully reset"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error processing request: {str(e)}"}), 500

# Logout route
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')