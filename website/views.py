from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, current_app
from flask_login import login_required, current_user, UserMixin
import os

views = Blueprint('views', __name__)

@views.route('/debug-templates')
def debug_templates():
    return jsonify(templates=current_app.jinja_env.list_templates())

# Home route
@views.route('/home')
def home():
    if 'user_id' not in session:
        return redirect('/login')
    # Debugging: Check if the template file exists
    template_path = os.path.join(current_app.root_path, "templates", "home.html")
    if not os.path.exists(template_path):
        return f"Error: Template file not found at {template_path}", 500

    return render_template('home.html', username=session.get('user_name', 'User'))

# Account route
@views.route('/account')
def account():
    if 'user_id' not in session:
        return redirect('/login?next=/account')
    
    try:
        from .__init__ import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
        user = cursor.fetchone()
        
        if not user:
            session.clear()
            return redirect('/login')
            
        return render_template('account.html', user=user)
    except Exception as e:
        return f"Error: {str(e)}", 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

#courses route
@views.route('/courses')
def courses():
    return render_template('courses.html')