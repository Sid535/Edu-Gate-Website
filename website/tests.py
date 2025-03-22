from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import Subject, Test
from .database import db
from .forms import TestForm

tests_bp = Blueprint('tests', __name__, url_prefix='/tests')

@tests_bp.route('/create/<int:subject_id>', methods=['GET', 'POST'])
@login_required
def create_test(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    course = subject.course  # Fetch course through the relationship

    if current_user.id != course.created_by:
        flash("You are not authorized to create tests for this subject.", "danger")
        return redirect(url_for('courses/courses.course-details', course_id=course.id))
    
    form = TestForm()

    if request.method == 'POST':
        test_name = request.form.get('test_name')

        new_test = Test(name=test_name, subject_id=subject_id)  # Assign subject_id
        db.session.add(new_test)
        db.session.commit()
        flash("Test created successfully!", "success")
        return redirect(url_for('tests/tests.take_test', test_id=new_test.id))

    return render_template('tests/create_test.html', subject=subject, course=course)  # Pass subject to the template


@tests_bp.route('/take_test/<int:test_id>')
@login_required
def take_test(test_id):
    try:
        test = Test.query.get_or_404(test_id)
    except Exception as e:
        flash(f"An error occurred while fetching the test: {str(e)}", "danger")
        return redirect(url_for('404.html'))

    return render_template('tests/take_test.html', test=test)

@tests_bp.route('/view_results/<int:test_id>')
@login_required
def view_results(test_id):
    try:
        test = Test.query.get_or_404(test_id)
    except Exception as e:
        flash(f"An error occurred while fetching the test: {str(e)}", "danger")
        return redirect(url_for('404.html'))

    return render_template('view_results.html', test=test)


@tests_bp.route('/edit_test/<int:test_id>')
@login_required
def edit_test(test_id):
    try:
        test = Test.query.get_or_404(test_id)
        form = TestForm(obj=test)  # Pre-populate the form with existing test data

        if form.validate_on_submit():  # Check if form is submitted and valid
            test.name = form.name.data  # Update test name from form data
            db.session.commit()
            flash("Test updated successfully!", "success")
            return redirect(url_for('tests.view_results', test_id=test.id))

    except Exception as e:
        flash(f"An error occurred while fetching or updating the test: {str(e)}", "danger")
        return redirect(url_for('404.html'))

    return render_template('tests/edit_test.html', form=form, test=test)  # Pass the form and test data to the template