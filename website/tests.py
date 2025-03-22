from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import Test, Question, Answer, TestAttempt, StudentAnswer, Subject
from .database import db
from .forms import TestForm

tests_bp = Blueprint('tests', __name__, url_prefix='/tests')

# Route to create a test
@tests_bp.route('/create/<int:subject_id>', methods=['GET', 'POST'])
@login_required
def create_test(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    course = subject.course  # Retrieve the associated course

    if current_user.id != subject.course.created_by:
        flash("You are not authorized to create tests for this subject.", "danger")
        return redirect(url_for('courses.course_details', course_id=subject.course_id))

    form = TestForm()

    if form.validate_on_submit():
        new_test = Test(
            name=form.name.data,
            subject_id=subject.id,
        )
        try:
            db.session.add(new_test)
            db.session.commit()
            flash("Test created successfully!", "success")
            return redirect(url_for('tests.manage_questions', test_id=new_test.id))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred while creating the test: {str(e)}", "danger")

    return render_template('tests/create_test.html', form=form, subject=subject, course=course)

# Route to take a test
@tests_bp.route('/take_test/<int:test_id>', methods=['GET', 'POST'])
@login_required
def take_test(test_id):
    test = Test.query.get_or_404(test_id)

    if request.method == 'POST':
        # Handle answer submission
        score = 0

        # Create a new test attempt record
        test_attempt = TestAttempt(test_id=test.id, student_id=current_user.id)
        db.session.add(test_attempt)
        db.session.commit()

        for question in test.questions:
            selected_answer_id = request.form.get(str(question.id))  # Get selected answer for each question
            is_correct = False

            if selected_answer_id:
                selected_answer = Answer.query.get(selected_answer_id)
                if selected_answer and selected_answer.is_correct:
                    is_correct = True
                    score += float(question.points)

            # Save the student's answer
            student_answer = StudentAnswer(
                attempt_id=test_attempt.id,
                question_id=question.id,
                selected_answer_id=selected_answer_id,
                is_correct=is_correct,
            )
            db.session.add(student_answer)

        # Update the score in the test attempt record
        test_attempt.score = score
        db.session.commit()

        flash(f"Test submitted successfully! Your score: {score}", "success")
        return redirect(url_for('tests.view_results', test_attempt_id=test_attempt.id))

    return render_template('tests/take_test.html', test=test)

# Route to view test results
@tests_bp.route('/view_results/<int:test_attempt_id>')
@login_required
def view_results(test_attempt_id):
    attempt = TestAttempt.query.get_or_404(test_attempt_id)
    if attempt.student_id != current_user.id:
        flash("You are not authorized to view these results.", "danger")
        return redirect(url_for('tests.take_test', test_id=attempt.test_id))

    student_answers = StudentAnswer.query.filter_by(attempt_id=attempt.id).all()
    return render_template('tests/view_results.html', attempt=attempt, student_answers=student_answers)

# Route to manage questions for a test
@tests_bp.route('/manage_questions/<int:test_id>', methods=['GET', 'POST'])
@login_required
def manage_questions(test_id):
    test = Test.query.get_or_404(test_id)
    
    if current_user.id != test.subject.course.created_by:
        flash("You are not authorized to manage questions for this test.", "danger")
        return redirect(url_for('subjects.view_subject', subject_id=test.subject.id))

    if request.method == 'POST':
        question_text = request.form.get('question_text')
        question_type = request.form.get('question_type')
        points = request.form.get('points')

        new_question = Question(
            test_id=test.id,
            text=question_text,
            question_type=question_type,
            points=float(points),
        )
        
        try:
            db.session.add(new_question)
            db.session.commit()
            flash("Question added successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred while adding the question: {str(e)}", "danger")
            
    questions = Question.query.filter_by(test_id=test.id).all()
    return render_template('tests/manage_questions.html', test=test, questions=questions)

# Route to edit a question
@tests_bp.route('/edit_question/<int:question_id>', methods=['GET', 'POST'])
@login_required
def edit_question(question_id):
    question = Question.query.get_or_404(question_id)
    test = question.test  # Get the associated test

    if request.method == 'POST':
        question.text = request.form.get('question_text')
        question.question_type = request.form.get('question_type')
        question.points = float(request.form.get('points'))

        try:
            db.session.commit()
            flash("Question updated successfully!", "success")
            return redirect(url_for('tests.manage_questions', test_id=test.id))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred while updating the question: {str(e)}", "danger")

    # Render form with existing question data
    return render_template('tests/edit_question.html', question=question, test=test)


# Route to delete a question
@tests_bp.route('/delete_question/<int:question_id>', methods=['POST'])
@login_required
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    test = question.test

    try:
        db.session.delete(question)
        db.session.commit()
        flash("Question deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while deleting the question: {str(e)}", "danger")

    return redirect(url_for('tests.manage_questions', test_id=test.id))
