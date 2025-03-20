#forms.py file
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length, URL  # Added URL validator


class EditCourseForm(FlaskForm):
    name = StringField('Course Name', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    image_path = StringField('Image Path', validators=[URL(require_tld=False), Length(max=200)])  # URL Field
    submit = SubmitField('Update Course')