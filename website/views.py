from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
import bcrypt
import os
import re
from .models import db, User
from .database import db

views = Blueprint('views', __name__)

@views.route('/debug-templates')
def debug_templates():
    return jsonify(templates=current_app.jinja_env.list_templates())

#courses route
@views.route('/courses')
def courses():
    return render_template('courses.html')

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
        user = User.query.get(current_user.id)
        
        if not user:
            from flask_login import logout_user
            logout_user()
            return redirect('/login')
            
        return render_template('account.html', user=user)
    except Exception as e:
        return f"Error: {str(e)}", 500

# Edit account route
@views.route('/account/edit', methods=['GET', 'POST'])
@login_required
def edit_account():
    try:
        user = User.query.get(current_user.id)
        
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('views.account'))
        
        # If it's a POST request, process the form data
        if request.method == 'POST':
            name = request.form.get('name')
            email = request.form.get('email')
            username = request.form.get('username')
            password = request.form.get('password')
            
            # Name validation
            if not re.match(r'^[a-zA-Z\s]+$', name):
                flash('Name should only contain letters and spaces', 'error')
                return render_template('edit_account.html', user=user)
            
            # Username validation
            if username and not re.match(r'^[a-zA-Z0-9_]+$', username):
                flash('Username should only contain letters, numbers, and underscores', 'error')
                return render_template('edit_account.html', user=user)
                
            # Email validation
            if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
                flash('Please enter a valid email address', 'error')
                return render_template('edit_account.html', user=user)
            
            # Check if the email is already taken by another user
            if email != user.email:
                existing_user = User.query.filter(User.email == email, User.id != user.id).first()
                if existing_user:
                    flash('Email address is already in use', 'error')
                    return render_template('edit_account.html', user=user)
            
            # Check if the username is already taken by another user
            if username and username != user.username:
                existing_user = User.query.filter(User.username == username, User.id != user.id).first()
                if existing_user:
                    flash('Username is already taken', 'error')
                    return render_template('edit_account.html', user=user)
                
            # Update user data
            user.name = name
            user.email = email
            if username:
                user.username = username
                
            # Password validation and update
            if password and password.strip():
                if len(password) < 6:
                    flash('Password must be at least 6 characters long', 'error')
                    return render_template('edit_account.html', user=user)
                # Hash the password
                user.password = User.hash_password(password)
                    
            # Save changes to database
            db.session.commit()
            
            # Update the current user session
            current_user.name = name
            current_user.email = email
            if username:
                current_user.username = username
            
            flash('Your account has been updated!', 'success')
            return redirect(url_for('views.account'))
        
        # If it's a GET request, display the form
        return render_template('edit_account.html', user=user)
    
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('views.account'))