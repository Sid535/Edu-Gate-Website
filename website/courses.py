# courses.py file
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, current_app
from flask_sqlalchemy import SQLAlchemy
from .database import db
from .models import Course, User
import logging  # Add this for debugging

courses_bp = Blueprint('courses', __name__, url_prefix='/courses')

@property
def image_filename(self):
    return self.image_path if self.image_path else 'default_course.jpg'

@courses_bp.route('/')
def all_courses():
    page = request.args.get('page', 1, type=int)
    per_page = 9  # Limit per page for scalability
    courses = Course.query.paginate(page=page, per_page=per_page, error_out=False)
    return render_template('courses.html', courses=courses.items, pagination=courses)

@courses_bp.route('/<int:course_id>')
def course_details(course_id):
    course = Course.query.get_or_404(course_id)

    return render_template('course-details.html', course=course)