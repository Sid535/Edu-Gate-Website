from flask import Flask, request, jsonify, render_template, session, redirect,url_for, flash,Blueprint
import mysql.connector
from mysql.connector import pooling
from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt
import uuid
import os
import hashlib
import smtplib
import secrets
from email.mime.text import MIMEText
from datetime import timedelta, datetime
from dotenv import load_dotenv
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from website import create_app
from flask_sqlalchemy import SQLAlchemy
from website.__init__ import get_db_connection  # If needed in a specific place

load_dotenv()

app = create_app()
app.secret_key = os.environ.get('SECRET_KEY')

print(app.url_map)

# Serve the login page
@app.route('/')
@app.route('/login', methods=['GET'])
def login_page():
    if current_user.is_authenticated:
        next_page = request.args.get('next', '/home')
        return redirect(next_page)
    return render_template('login.html')


# Handle login API request
@app.route('/api/login', methods=['POST'])
def login_api():
    data = request.get_json()
    
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({"message": "Missing email or password"}), 400
    
    email = data['email']
    password = data['password'].encode('utf-8')
    
    try:
        from website import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user_data = cursor.fetchone()
    except Exception as e:
        return jsonify({"message": f"Database error: {str(e)}"}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

    if not user_data:
        return jsonify({"message": "Invalid email or password"}), 401

    # Verify password
    stored_password = user_data['password'].encode('utf-8') if isinstance(user_data['password'], str) else user_data['password']
    if bcrypt.checkpw(password, stored_password):
        # Create User object for Flask-Login
        from website import User
        user = User(user_data["id"], user_data["name"], user_data["email"], user_data["username"])
        login_user(user, remember=True)
        
        # Set session duration
        app.permanent_session_lifetime = timedelta(days=30)
        session.permanent = True

        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"message": "Invalid email or password"}), 401

# Registration page
@app.route('/signup')
def signup_page():
    return render_template('signup.html')


# Handle registration API
# Handle registration API
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data or 'name' not in data or 'email' not in data or 'password' not in data or 'username' not in data:
        return jsonify({"message": "Missing required fields"}), 400

    name = data['name']
    email = data['email']
    username = data['username']
    password = data['password'].encode('utf-8')

    # Hash the password with bcrypt
    hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())

    try:
        from website import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if email already exists
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({"message": "Email already registered"}), 409
        
        # Check if username already exists
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return jsonify({"message": "Username already taken"}), 409

        # Insert new user
        cursor.execute("INSERT INTO users (name, email, password, username) VALUES (%s, %s, %s, %s)",
                       (name, email, hashed_password.decode('utf-8'), username))
        conn.commit()
        user_id = cursor.lastrowid
        
        # Get the full user data
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user_data = cursor.fetchone()
    except Exception as e:
        return jsonify({"message": f"Registration error: {str(e)}"}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

    # Log the user in with Flask-Login
    from website import User
    user = User(user_id, name, email, username)
    login_user(user, remember=True)

    return jsonify({"message": "Registration successful"}), 201

# Forgot Password page
@app.route('/forgot-password')
def forgot_password_page():
    return render_template('forgot-password.html')


# Handle forgot password request
@app.route('/api/forgot-password', methods=['POST'])
def forgot_password_api():
    data = request.get_json()
    
    if not data or 'email' not in data:
        return jsonify({"message": "Email is required"}), 400
    
    email = data['email']
    
    try:
        from website import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if not user:
            # Don't reveal if email exists or not for security
            return jsonify({"message": "If your email exists in our system, you will receive a password reset link"}), 200
        
        # Generate a reset token
        reset_token = str(uuid.uuid4())
        expiry = datetime.now() + timedelta(hours=24)
        
        # Store the reset token in the database
        cursor.execute("""
            INSERT INTO password_resets (user_id, token, expires_at) 
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE token = %s, expires_at = %s
        """, (user['id'], reset_token, expiry, reset_token, expiry))
        conn.commit()
        print(f"Reset token: {reset_token}") #debugging line
        
        # Create a reset link
        reset_link = f"{request.host_url}reset-password/{reset_token}"
        
        # Send email with reset link
        send_password_reset_email(email, reset_link, user['name'])
        
        return jsonify({"message": "If your email exists in our system, you will receive a password reset link"}), 200
    except Exception as e:
        return jsonify({"message": f"Error processing request: {str(e)}"}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# Function to send password reset email
def send_password_reset_email(email, reset_link, name):
    try:
        # Get email configuration from environment variables
        smtp_server = os.environ.get('SMTP_SERVER')
        smtp_port = os.environ.get('SMTP_PORT')
        smtp_username = os.environ.get('SMTP_USERNAME')
        smtp_password = os.environ.get('SMTP_PASSWORD')
        sender_email = os.environ.get('SENDER_EMAIL', 'noreply@yourdomain.com')
        
        # For development/testing: print the link instead of sending email
        if not all([smtp_server, smtp_port, smtp_username, smtp_password]):
            print(f"===== PASSWORD RESET LINK =====")
            print(f"For user: {name} ({email})")
            print(f"Link: {reset_link}")
            print(f"===============================")
            return
            
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
        
        print(f"Password reset email sent to {email}")
        
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        # Log this error, but don't expose to user

@app.route('/reset-password/<token>', methods=['GET'])
def reset_password_page(token):
    return render_template('reset-password.html', token=token)

# Handle password reset
@app.route('/api/reset-password', methods=['POST'])
def reset_password_api():
    data = request.get_json()
    
    if not data or 'token' not in data or 'password' not in data:
        return jsonify({"message": "Token and password are required"}), 400
    
    token = data['token']
    password = data['password']
    
    try:
        from website import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Find the valid token
        cursor.execute("""
            SELECT pr.*, u.email 
            FROM password_resets pr
            JOIN users u ON pr.user_id = u.id
            WHERE pr.token = %s AND pr.expires_at > NOW()
        """, (token,))
        
        reset_request = cursor.fetchone()
        
        if not reset_request:
            return jsonify({"message": "Invalid or expired token"}), 400
        
        # Hash the new password using bcrypt
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Update the user's password
        cursor.execute("UPDATE users SET password = %s WHERE id = %s", 
              (hashed_password.decode('utf-8'), reset_request['user_id']))

        # Delete the used token
        cursor.execute("DELETE FROM password_resets WHERE id = %s", (reset_request['id'],))
        
        conn.commit()
        
        return jsonify({"message": "Password successfully reset"}), 200
    except Exception as e:
        return jsonify({"message": f"Error processing request: {str(e)}"}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# Logout route using Flask-Login
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', '').lower() in ['1', 'true', 'yes']
    app.run(debug=debug_mode)