from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import Course, Test
from .database import db

tests_bp = Blueprint('tests', __name__, url_prefix='/tests')

@tests_bp.route('/create/<int:course_id>', methods=['GET', 'POST'])
@login_required
def create_test(course_id):
    course = Course.query.get_or_404(course_id)
    if current_user.id != course.created_by:
        flash("You are not authorized to create tests for this course.", "danger")
        return redirect(url_for('courses.course_details', course_id=course_id))

    if request.method == 'POST':
        # Extract form data and create a new test
        test_name = request.form.get('test_name')
        # Add more fields as necessary
        new_test = Test(name=test_name, course_id=course_id, created_by=current_user.id)
        db.session.add(new_test)
        db.session.commit()
        flash("Test created successfully!", "success")
        return redirect(url_for('tests.take_test', test_id=new_test.id))

    return render_template('create_test.html', course=course)


@tests_bp.route('/take_test/<int:test_id>')
@login_required
def take_test(test_id):
    # Fetch the test based on test_id
    try:
        test = Test.query.get_or_404(test_id)
    except Exception as e:
        flash(f"An error occurred while fetching the test: {str(e)}", "danger")
        return redirect(url_for('404.html'))
    # You can add logic here to fetch specific content related to the test
    return render_template('take_test.html', test=test)


@tests_bp.route('/view_results/<int:test_id>')
@login_required
def view_results(test_id):
    # Fetch the test based on test_id
    try:
        test = Test.query.get_or_404(test_id)
    except Exception as e:
        flash(f"An error occurred while fetching the test: {str(e)}", "danger")
        return redirect(url_for('404.html'))
    # You can add logic here to fetch specific content related to the test
    return render_template('view_results.html', test=test)


@tests_bp.route('/edit_test/<int:test_id>')
@login_required
def edit_test(test_id):
    # Fetch the test based on test_id
    try:
        test = Test.query.get_or_404(test_id)
    except Exception as e:
        flash(f"An error occurred while fetching the test: {str(e)}", "danger")
        return redirect(url_for('404.html'))
    # You can add logic here to fetch specific content related to the test
    return render_template('edit_test.html', test=test)

