from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, current_app
from flask_sqlalchemy import SQLAlchemy

course_data = Blueprint('course_data', __name__)

# Course data
courses = [
    {
        'id': 'aerospace-engineering',
        'title': 'Aerospace Engineering',
        'description': 'Aerospace engineering is a field of engineering focused on the design, development, testing, and maintenance of aircraft and spacecraft...',
        'image': 'images/aerospace-engineering.jpg'
    },
    # Add all your courses here...
]
