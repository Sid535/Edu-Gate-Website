from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from .database import db
from .models import Course, User, Test, TestAttempt
from .forms import EditCourseForm
import logging  # Add this for debugging

courses_bp = Blueprint('courses', __name__, url_prefix='/courses')

@courses_bp.route('/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)

    if current_user.id != course.created_by:
        flash("You are not authorized to edit this course.", "danger")
        return redirect(url_for('courses.course_details', course_id=course.id))

    form = EditCourseForm(obj=course)

    if form.validate_on_submit():
        course.name = form.name.data
        course.description = form.description.data
        course.image_path = form.image_path.data  # Update the image_path directly

        db.session.commit()
        flash("Course updated successfully!", "success")
        return redirect(url_for('courses.course_details', course_id=course.id))

    return render_template('edit_course.html', course=course, form=form)

@courses_bp.route('/<int:course_id>/content')
def course_content(course_id):
    # Fetch the course content based on course_id
    course = Course.query.get_or_404(course_id)
    # You can add logic here to fetch specific content related to the course
    return render_template('course_content.html', course=course)


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

    # Fetch tests associated with the course
    tests = Test.query.filter_by(course_id=course_id).all()

    # Fetch the user's test attempts for the current course
    test_attempts = []
    if current_user.is_authenticated:
        test_attempts = TestAttempt.query.filter_by(
            test_id=Test.id,  # Access test_id correctly
            student_id=current_user.id
        ).all()
    return render_template('course-details.html',
                           course=course,
                           tests=tests,
                           test_attempts=test_attempts,
                           current_user=current_user)
