from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, Flash
views = Blueprint('views', __name__)

# home route
@views.route('/home')
def home():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('home.html', username=session.get('user_name', 'User'))