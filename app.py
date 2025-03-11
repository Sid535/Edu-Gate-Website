from flask import Flask, request, jsonify, render_template, session, redirect,url_for
import mysql.connector
from mysql.connector import pooling
import bcrypt
import os
import smtplib
import secrets
from email.mime.text import MIMEText
from datetime import timedelta, datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')

# Database connection pool
db_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=5,
    host=os.environ.get('DB_HOST', 'localhost'),
    user=os.environ.get('DB_USER', 'root'),
    password=os.environ.get('DB_PASSWORD', '12082005'),
    database=os.environ.get('DB_NAME', 'edugate')
)

# Get connection from pool
def get_db_connection():
    return db_pool.get_connection()

# Serve the login page
@app.route('/')
@app.route('/login', methods=['GET'])
def login_page():
    if 'user_id' in session:
        return redirect('/dashboard')
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
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
    except Exception as e:
        return jsonify({"message": f"Database error: {str(e)}"}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

    if not user:
        return jsonify({"message": "Invalid email or password"}), 401

    # Verify password
    stored_password = user['password'].encode('utf-8') if isinstance(user['password'], str) else user['password']
    if bcrypt.checkpw(password, stored_password):
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session.permanent = True
        app.permanent_session_lifetime = timedelta(days=30)

        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"message": "Invalid email or password"}), 401

# Dashboard route
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('dashboard.html', username=session.get('user_name', 'User'))

# Registration page
@app.route('/signup')
def signup_page():
    return render_template('signup.html')


# Handle registration API
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data or 'name' not in data or 'email' not in data or 'password' not in data:
        return jsonify({"message": "Missing required fields"}), 400

    name = data['name']
    email = data['email']
    password = data['password'].encode('utf-8')

    # Hash the password
    hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if email already exists
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({"message": "Email already registered"}), 409

        # Insert new user
        cursor.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                       (name, email, hashed_password.decode('utf-8')))
        conn.commit()
        user_id = cursor.lastrowid
    except Exception as e:
        return jsonify({"message": f"Registration error: {str(e)}"}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

    # Log the user in
    session['user_id'] = user_id
    session['user_name'] = name

    return jsonify({"message": "Registration successful"}), 201

# forgot password page
@app.route('/forgot-password')
def forgot_password_page():
    if 'user_id' in session:
        return redirect('/dashboard')
    return render_template('forgot-password.html')

# Forgot password API
@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({"message": "Email is required"}), 400

    try:
        conn = db_pool.get_connection()
        cursor = conn.cursor()

        # Check if the email exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"message": "Email not found"}), 404

        # Generate a reset token
        reset_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=1) # Token valid for 1 hour
        
        print(f"Generated reset token: {reset_token}")  # Debugging line

        # Store the reset token in the database
        cursor.execute(
            "INSERT INTO password_reset_tokens (email, token, expires_at) VALUES (%s, %s, %s)",
            (email, reset_token, expires_at)
        )
        conn.commit()
        
        print("Token saved in database!")  # Debugging line

        # Send email with the reset link
        reset_link = url_for("reset_password", _external=True) + f"?token={reset_token}"
        send_reset_email(email, reset_link)

        return jsonify({"message": "Reset link sent! Check your email."}), 200

    except Exception as e:
        print(f"Database error: {str(e)}")  # Debugging line
        return jsonify({"message": f"Database error: {str(e)}"}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# Load from environment
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def send_reset_email(to_email, reset_link):
    subject = "Password Reset Request"
    body = f"Click the link below to reset your password:\n\n{reset_link}\n\nIf you didn't request this, ignore this email."

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = to_email
    
    print(f"Sending email to {to_email} with reset link: {reset_link}")  # Debugging line

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, to_email, msg.as_string())
        server.quit()
        print("Email sent successfully!")  # Debugging line
    except Exception as e:
        print(f"Failed to send email: {str(e)}")

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    token = data.get("token")
    new_password = data.get("password")

    if not token or not new_password:
        return jsonify({"message": "Invalid request"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM password_reset_tokens WHERE token = %s AND expires_at > NOW()", (token,))
        reset_entry = cursor.fetchone()
    except Exception as e:
        return jsonify({"message": f"Database error: {str(e)}"}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

    if not reset_entry:
        return jsonify({"message": "Invalid or expired token"}), 400

    email = reset_entry["email"]

    # Hash new password
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password = %s WHERE email = %s", (hashed_password, email))
        conn.commit()
    except Exception as e:
        return jsonify({"message": f"Database error: {str(e)}"}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

    cursor.execute("DELETE FROM password_resets WHERE email = %s", (email,))  # Remove used token
    conn.commit()
    
    return jsonify({"message": "Password reset successful!", "success": True})


# Logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true')
