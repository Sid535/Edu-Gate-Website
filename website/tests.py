from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import Test, Question, Answer, TestAttempt, StudentAnswer, Subject
from .database import db
from .forms import TestForm, AnswerForm, QuestionForm

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
# Route to manage questions for a test
@tests_bp.route('/manage_questions/<int:test_id>', methods=['GET', 'POST'])
@login_required
def manage_questions(test_id):
    test = Test.query.get_or_404(test_id)
    subject = test.subject
    course = subject.course
    
    if current_user.id != test.subject.course.created_by:
        flash("You are not authorized to manage questions for this test.", "danger")
        return redirect(url_for('subjects.view_subject', subject_id=test.subject.id))

    form = TestForm()  # Initialize the form
    form = QuestionForm()

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
            
            # Add answers for the newly created question
            answer_texts = request.form.getlist('answer_text')  # List of answer texts
            is_corrects = request.form.getlist('is_correct') # List of is_correct values
            
            for i, answer_text in enumerate(answer_texts):
                if answer_text:
                    # Check if this answer is marked as correct
                    is_correct = str(i) in is_corrects
                    
                    new_answer = Answer(
                        question_id=new_question.id,
                        text=answer_text,
                        is_correct=is_correct
                    )
                    db.session.add(new_answer)

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred while adding the question: {str(e)}", "danger")
            
    questions = Question.query.filter_by(test_id=test.id).all()
    return render_template('tests/manage_questions.html', test=test, questions=questions, course=course, subject=subject, form=form)


# Route to edit test(eg: test name)
@tests_bp.route('/edit_test/<int:test_id>', methods=['GET', 'POST'])
@login_required
def edit_test(test_id):
    test = Test.query.get_or_404(test_id)
    form = TestForm(obj=test)  # Used for displaying data

    # Authorization check
    if current_user.id != test.subject.course.created_by:
        flash("Unauthorized to edit this test", "danger")
        return redirect(url_for('subjects.view_subject', subject_id=test.subject.id))

    if request.method == 'POST':
        # Apply form validation
        if form.validate_on_submit():
            test.name = form.name.data

            try:
                db.session.commit()
                flash("Test updated successfully!", "success")
                return redirect(url_for('tests.manage_questions', test_id=test.id))
            except Exception as e:
                db.session.rollback()
                flash(f"An error occurred while updating the test: {str(e)}", "danger")
    return render_template('tests/edit_test.html', test=test, form=form)


# Route to edit a question
@tests_bp.route('/edit_question/<int:question_id>', methods=['GET', 'POST'])
@login_required
def edit_question(question_id):
    question = Question.query.get_or_404(question_id)
    test = question.test  # Get the associated test
    answers = question.answers  # Fetch existing answers
    subject = test.subject  # Get the associated subject
    course = subject.course  # Get the associated course

    if request.method == 'POST':
        # Update question details
        question.text = request.form.get('question_text')
        question.question_type = request.form.get('question_type')
        question.points = float(request.form.get('points'))

        # Process answers
        for answer in answers:
            answer_text = request.form.get(f'answer_text_{answer.id}')
            is_correct = f'is_correct_{answer.id}' in request.form
            
            answer.text = answer_text
            answer.is_correct = is_correct

        try:
            db.session.commit()
            flash("Question and answers updated successfully!", "success")
            return redirect(url_for('tests.manage_questions', test_id=test.id))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred while updating the question: {str(e)}", "danger")

    # Render form with existing question data and answers
    return render_template('tests/edit_question.html', question=question, test=test, answers=answers, course=course, subject=subject)

# Route to delete a question
@tests_bp.route('/delete_question/<int:question_id>', methods=['POST'])
@login_required
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    test = question.test

    try:
        db.session.delete(question)
        db.session.commit()
        print(f"Question with ID {question_id} deleted successfully.")
        flash("Question deleted successfully!", "success")
        print(f"3Attempting to delete question with ID: {question_id}")  # Debug statement
    except Exception as e:
        db.session.rollback()
        print(f"Error occurred: {str(e)}")  # Print error details
        flash(f"An error occurred while deleting the question: {str(e)}", "danger")
    
    return redirect(url_for('tests.manage_questions', test_id=test.id))
