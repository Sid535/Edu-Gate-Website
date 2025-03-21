from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from .database import db
from .models import Course, User, Test, TestAttempt, Subject  # Import Subject model
from .forms import EditCourseForm

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

    # Fetch subjects associated with the course
    subjects = Subject.query.filter_by(course_id=course.id).all()

    # Fetch the user's test attempts for each subject
    test_attempts_by_subject = {}
    
    if current_user.is_authenticated:
        for subject in subjects:
            test_attempts_by_subject[subject.id] = TestAttempt.query.filter(
                TestAttempt.student_id == current_user.id,
                TestAttempt.test.has(subject_id=subject.id)  # Filter by subject ID
            ).all()

    return render_template('course-details.html',
                           course=course,
                           subjects=subjects,
                           test_attempts_by_subject=test_attempts_by_subject,
                           current_user=current_user)
