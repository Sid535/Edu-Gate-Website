#forms.py file
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, IntegerField, SelectField
from wtforms.validators import DataRequired, Length, URL, NumberRange

class EditCourseForm(FlaskForm):
    name = StringField('Course Name', validators=[
        DataRequired(message='Course name is required.'),
        Length(min=2, max=100, message='Course name must be between 2 and 100 characters.')
    ])
    description = TextAreaField('Description', validators=[DataRequired(message='Description is required.')])
    image_path = StringField('Image Path', validators=[Length(max=200)])  # URL Field
    submit = SubmitField('Update Course')
    
class SubjectForm(FlaskForm):
    name = StringField('Name', validators=[
        DataRequired(message='Subject name is required.')
    ])
    description = TextAreaField('Description', validators=[
        DataRequired(message='Description is required.')
    ])
    sequence = IntegerField('Sequence', validators=[
        DataRequired(message='Sequence is required.'), 
        NumberRange(min=1, message='Sequence must be at least 1.')
    ]) # Assuming sequence starts from 1
    submit = SubmitField('Submit')
    
class TestForm(FlaskForm):
    name = StringField('Test Name', validators=[
        DataRequired(message='Please enter a test name.'),
        Length(min=2, max=100, message='Test name must be between 2 and 100 characters.')
    ])
    submit = SubmitField('Save Test')
    
class QuestionForm(FlaskForm):
    question_text = StringField('Question Text', validators=[DataRequired()])
    question_type = SelectField('Question Type', choices=[
        ('MCQ', 'Multiple Choice'),
        ('True/False', 'True/False'),
        ('Short Answer', 'Short Answer')
    ], validators=[DataRequired()])
    points = IntegerField('Points', default=1, validators=[DataRequired()])
    submit = SubmitField('Add Question')