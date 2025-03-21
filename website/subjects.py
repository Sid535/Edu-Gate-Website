from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import Course, Subject
from .database import db

subjects_bp = Blueprint('subjects', __name__, url_prefix='/subjects')

# Route to create a new subject
@subjects_bp.route('/create/<int:course_id>', methods=['GET', 'POST'])
@login_required
def create_subject(course_id):
    course = Course.query.get_or_404(course_id)
    if current_user.id != course.created_by:
        flash("You are not authorized to add subjects to this course.", "danger")
        return redirect(url_for('courses.course_details', course_id=course.id))

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        sequence = request.form.get('sequence')  # You might want to provide a form field for this

        if name and description and sequence:
            new_subject = Subject(name=name, description=description, course_id=course.id, sequence=sequence)
            db.session.add(new_subject)
            db.session.commit()
            flash('Subject created successfully!', 'success')
            return redirect(url_for('courses.course_details', course_id=course.id))
        else:
            flash('Please fill in all the required fields.', 'danger')

    return render_template('subjects/create_subject.html', course=course)

# Route to view a specific subject
@subjects_bp.route('/view/<int:subject_id>')
def view_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    return render_template('subjects/view_subject.html', subject=subject)

# Route to edit an existing subject
@subjects_bp.route('/edit/<int:subject_id>', methods=['GET', 'POST'])
@login_required
def edit_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    course = Course.query.get_or_404(subject.course_id)
    
    if current_user.id != course.created_by:
        flash("You are not authorized to edit this subject.", "danger")
        return redirect(url_for('courses.course_details', course_id=course.id))
    
    if request.method == 'POST':
        subject.name = request.form.get('name')
        subject.description = request.form.get('description')
        subject.sequence = request.form.get('sequence')
        
        db.session.commit()
        flash('Subject updated successfully!', 'success')
        return redirect(url_for('courses.course_details', course_id=course.course_id))
    
    return render_template('subjects/edit_subject.html', subject=subject)

# Route to delete a subject
@subjects_bp.route('/delete/<int:subject_id>')
@login_required
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    course_id = subject.course_id
    course = Course.query.get_or_404(course_id)

    if current_user.id != course.created_by:
        flash("You are not authorized to delete this subject.", "danger")
        return redirect(url_for('courses.course_details', course_id=course.id))

    db.session.delete(subject)
    db.session.commit()
    flash('Subject deleted successfully!', 'success')
    return redirect(url_for('courses.course_details', course_id=course_id))