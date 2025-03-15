from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, current_app
from flask_login import login_required, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
import bcrypt
import os

views = Blueprint('views', __name__)

@views.route('/debug-templates')
def debug_templates():
    return jsonify(templates=current_app.jinja_env.list_templates())

# Home route
@views.route('/home')
@login_required
def home():
    return render_template('home.html', username=current_user.name)

# Account route
@views.route('/account')
@login_required
def account():
    try:
        from website import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (current_user.id,))
        user = cursor.fetchone()
        
        if not user:
            from flask_login import logout_user
            logout_user()
            return redirect('/login')
            
        return render_template('account.html', user=user)
    except Exception as e:
        return f"Error: {str(e)}", 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# Edit account route
@views.route('/account/edit', methods=['GET', 'POST'])
@login_required
def edit_account():
    try:
        from website import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get current user data - using Flask-Login's current_user
        user_id = current_user.id
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('views.account'))
        
        # If it's a POST request, process the form data
        if request.method == 'POST':
            name = request.form.get('name')
            email = request.form.get('email')
            password = request.form.get('password')
            
            # Update user information in database
            if password and password.strip():
                # Use bcrypt for password hashing consistently
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                cursor.execute(
                    "UPDATE users SET name = %s, email = %s, password = %s WHERE id = %s",
                    (name, email, hashed_password, user_id)
                )
            else:
                cursor.execute(
                    "UPDATE users SET name = %s, email = %s WHERE id = %s",
                    (name, email, user_id)
                )
            
            conn.commit()
            
            # Update the current_user object - this doesn't work directly with Flask-Login's implementation
            # We need to reload the user on next request
            
            flash('Your account has been updated!', 'success')
            return redirect(url_for('views.account'))
        
        # If it's a GET request, display the form
        return render_template('edit_account.html', user=user)
    
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('views.account'))
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

#courses route
@views.route('/courses')
def courses():
    return render_template('courses.html')

