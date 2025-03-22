#forms.py file
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length, URL, NumberRange
from flask_wtf import FlaskForm

class EditCourseForm(FlaskForm):
    name = StringField('Course Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    image_path = StringField('Image Path', validators=[URL(require_tld=False), Length(max=200)])  # URL Field
    submit = SubmitField('Update Course')
    
class SubjectForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    sequence = IntegerField('Sequence', validators=[DataRequired(), NumberRange(min=1)]) # Assuming sequence starts from 1
    submit = SubmitField('Submit')
    
class TestForm(FlaskForm):
    name = StringField('Test Name', validators=[
        DataRequired(message='Please enter a test name.'),
        Length(min=2, max=100, message='Test name must be between 2 and 100 characters.')
    ])
    submit = SubmitField('Save Test')