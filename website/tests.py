from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import Test, Question, Answer, TestAttempt, StudentAnswer, Subject
from .database import db
from .forms import TestForm, AnswerForm, QuestionForm
from bokeh.embed import components
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.plotting import figure
from collections import defaultdict
from decimal import Decimal
from math import pi

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
        return redirect(url_for('subjects.view_subject', subject_id=test.subject.id))

    return render_template('tests/take_test.html', test=test)

# Route to view test results
@tests_bp.route('/view_results/<int:test_attempt_id>')
@login_required
def view_results(test_attempt_id):
    attempt = TestAttempt.query.get_or_404(test_attempt_id)
    
    # Check if the current user is authorized to view this attempt
    if attempt.student_id != current_user.id:
        flash("You are not authorized to view these results.", "danger")
        return redirect(url_for('tests.take_test', test_id=attempt.test_id))

    # Fetch student answers for this test attempt
    student_answers = StudentAnswer.query.filter_by(attempt_id=attempt.id).all()
    
    # Prepare data for visualizations
    correct = sum(1 for ans in student_answers if ans.is_correct)
    incorrect = sum(1 for ans in student_answers if ans.is_correct is False)
    unattempted = sum(1 for ans in student_answers if ans.is_correct is None)
    
    question_types = ["Correct", "Incorrect", "Unattempted"]
    values = [correct, incorrect, unattempted]
    colors_pie = ["green", "red", "blue"]
    
    # Pie Chart for Question Statistics
    data_pie = ColumnDataSource(data=dict(
        question_types=question_types,
        values=values,
        colors=colors_pie,
        start_angle=[sum(values[:i]) / sum(values) * 2 * 3.14159 for i in range(len(values))],
        end_angle=[sum(values[:i + 1]) / sum(values) * 2 * 3.14159 for i in range(len(values))]
    ))

    p_pie = figure(height=350, width=400, title="Question Statistics", toolbar_location=None,
                   tools="hover", tooltips="@question_types: @values", x_range=(-1, 1))
    
    p_pie.wedge(x=0, y=0, radius=0.8,
                start_angle='start_angle',
                end_angle='end_angle',
                line_color="white",
                fill_color='colors',
                legend_field="question_types",
                source=data_pie)
    
    p_pie.axis.visible = False
    p_pie.grid.visible = False
    
    # Subject-wise Marks Bar Chart
    subject_points = defaultdict(Decimal)
    subject_total_points = defaultdict(Decimal)

    for answer in student_answers:
        subject_name = answer.question.test.subject.name
        
        points = Decimal(str(answer.question.points))
        
        if answer.is_correct:
            subject_points[subject_name] += points
        subject_total_points[subject_name] += points

    # Prepare data for bar chart
    subjects = list(subject_points.keys())
    
    # Handle cases with no subjects or marks gracefully
    if not subjects:
        subjects = ["No Subjects"]
        marks = [0]
        total_marks = [0]
        colors = ["grey"]
    else:
        marks = [float(subject_points.get(subject, 0)) for subject in subjects]
        total_marks = [float(subject_total_points.get(subject, 0)) for subject in subjects]
        colors = ["blue", "green", "orange", "red"][:len(subjects)]

    # Use a more robust method to create ColumnDataSource
    source = ColumnDataSource(data=dict(
        subjects=subjects,
        marks=marks,
        total_marks=total_marks,
        colors=colors
    ))
    
    p_marks = figure(
        x_range=subjects,
        height=350,
        width=400,
        title="Subject-wise Performance",
        x_axis_label="Subjects",
        y_axis_label="Points",
        toolbar_location=None
    )
    
    p_marks.vbar(
        x='subjects',  # Ensure this matches the column name
        top='marks',   # Ensure this matches the column name
        width=0.6,
        color='colors',
        source=source,
        legend_label="Earned Points"
    )
    
    # Use a more careful line method
    p_marks.line(
        x='subjects',
        y='total_marks',
        line_width=2,
        color="black",
        line_dash="dashed",
        source=source,
        legend_label="Total Possible Points"
    )
    
    p_marks.legend.location = "top_right"
    p_marks.legend.click_policy = "hide"

    # Add hover tool to the bar chart
    hover = HoverTool(tooltips=[
        ("Subject", "@subjects"),
        ("Earned Points", "@marks"),
        ("Total Points", "@total_marks")
    ])
    
    p_marks.add_tools(hover)

    # Embed Bokeh Components into the template
    script_pie, div_pie = components(p_pie)
    script_marks, div_marks = components(p_marks)

    return render_template('tests/view_results.html', 
                           attempt=attempt, 
                           student_answers=student_answers,
                           script_pie=script_pie, 
                           div_pie=div_pie,
                           script_marks=script_marks, 
                           div_marks=div_marks,
                           total_score=float(attempt.score),
                           total_possible_score=float(attempt.test.total_points))

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
            
            for i, answer_text in enumerate(answer_texts):
                if answer_text:
                    # Check if this answer is marked as correct
                    is_correct = request.form.get(f'is_correct_{i}') == 'on'
                    
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


# Route to edit a question
@tests_bp.route('/edit_question/<int:question_id>', methods=['GET', 'POST'])
@login_required
def edit_question(question_id):
    question = Question.query.get_or_404(question_id)
    test = question.test
    answers = question.answers
    subject = test.subject
    course = subject.course

    if request.method == 'POST':
        # Update question details
        question.text = request.form.get('question_text')
        question.question_type = request.form.get('question_type')
        question.points = float(request.form.get('points'))

        # Process answers
        for i, answer in enumerate(answers):
            answer_text = request.form.get(f'answer_text_{answer.id}')
            is_correct = request.form.get(f'is_correct_{i}') == 'on'
            
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
