from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, current_app
from flask_login import login_required, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy
import bcrypt
import datetime
import os

# Initialize SQLAlchemy
db = SQLAlchemy()
model = Blueprint('model', __name__)

# Model definitions
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=True)
    password = db.Column(db.String(100), nullable=False)
    
    # Relationships
    password_resets = db.relationship('PasswordReset', backref='user', lazy=True)
    
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
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    def is_expired(self):
        return datetime.datetime.now() > self.expires_at


# Function to get user by ID for Flask-Login
def load_user(user_id):
    return User.query.get(int(user_id))