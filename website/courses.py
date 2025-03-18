# courses.py file
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, current_app
from flask_sqlalchemy import SQLAlchemy
from .database import db
from .models import Course, User
from dotenv import load_dotenv

load_dotenv()

courses_bp = Blueprint('courses', __name__)

@courses_bp.route('/<int:course_id>')
def view_course(course_id):
    # Query the database to get the course with the given ID
    course = Course.query.get_or_404(course_id)
    # Now pass the retrieved course to the template
    return render_template('course_detail.html', course=course)

@courses_bp.route('/')
def list_courses():
    try:
        courses = Course.query.all()
        print(f"Number of courses retrieved: {len(courses)}")
        
        # Debug: Print the first few courses
        for i, course in enumerate(courses[:3]):
            print(f"Course {i}: {course.name}")
            
        return render_template('courses.html', courses=courses)
    except Exception as e:
        print(f"Error in list_courses: {e}")
        import traceback
        traceback.print_exc()
        return render_template('courses.html', courses=[])