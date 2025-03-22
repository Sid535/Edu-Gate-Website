from flask import Flask
from flask_login import UserMixin, LoginManager
from flask_sqlalchemy import SQLAlchemy
import bcrypt
import datetime
from flask_login import login_required, current_user, UserMixin
import bcrypt
import datetime
from .database import db

# Model definitions
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=True)
    password = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    
    # Relationships
    password_resets = db.relationship('PasswordReset', backref='user', lazy=True)
    created_courses = db.relationship('Course', backref='creator', lazy=True, foreign_keys='Course.created_by')
    test_attempts = db.relationship('TestAttempt', backref='student', lazy=True)
    
    def __init__(self, id=None, name=None, email=None, username=None):
        if id is not None:
            self.id = id
        if name is not None:
            self.name = name
        if email is not None:
            self.email = email
        if username is not None:
            self.username = username
    
    def check_password(self, password):
        stored_password = self.password.encode('utf-8') if isinstance(self.password, str) else self.password
        return bcrypt.checkpw(password.encode('utf-8'), stored_password)
    
    @staticmethod
    def hash_password(password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

class PasswordReset(db.Model):
    __tablename__ = 'password_resets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    token = db.Column(db.String(255), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    
    def is_expired(self):
        return datetime.datetime.now() > self.expires_at
    
class Course(db.Model):
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    image_path = db.Column(db.String(255), nullable=True)

    # Relationships
    subjects = db.relationship('Subject', backref='course', lazy=True, cascade='all, delete-orphan')  # Relationship to subjects

class Subject(db.Model):
    __tablename__ = 'subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    sequence = db.Column(db.Integer, nullable=False)  # To order subjects within a course
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    
    # Relationships
    tests = db.relationship('Test', backref='subject', lazy=True, cascade='all, delete-orphan')

class Test(db.Model):
    __tablename__ = 'tests'
    
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False)  # Updated from course_id to subject_id
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    
    # Relationships
    questions = db.relationship('Question', backref='test', lazy=True, cascade='all, delete-orphan')
    attempts = db.relationship('TestAttempt', backref='test', lazy=True, cascade='all, delete-orphan')

class TestAttempt(db.Model):
    __tablename__ = 'test_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id', ondelete='CASCADE'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    score = db.Column(db.DECIMAL(5, 2), nullable=True)
    attempt_date = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())
    
    # Relationships
    student_answers = db.relationship('StudentAnswer', backref='attempt', lazy=True, cascade='all, delete-orphan')


class Question(db.Model):
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id', ondelete='CASCADE'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.Enum('MCQ', 'True/False', 'Short Answer'), nullable=False, default='MCQ')
    points = db.Column(db.DECIMAL(5, 2), nullable=False, default=1.00)
    
    # Relationships
    answers = db.relationship('Answer', backref='question', lazy=True, cascade='all, delete-orphan')
    student_answers = db.relationship('StudentAnswer', backref='question', lazy=True)


class Answer(db.Model):
    __tablename__ = 'answers'
    
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id', ondelete='CASCADE'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    
    # Relationships
    student_selections = db.relationship('StudentAnswer', backref='selected_answer', lazy=True)

class StudentAnswer(db.Model):
    __tablename__ = 'student_answers'
    
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('test_attempts.id', ondelete='CASCADE'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id', ondelete='CASCADE'), nullable=False)
    selected_answer_id = db.Column(db.Integer, db.ForeignKey('answers.id', ondelete='SET NULL'), nullable=True)
    is_correct = db.Column(db.Boolean, nullable=True)

# Function to get user by ID for Flask-Login
def load_user(user_id):
    return User.query.get(int(user_id))