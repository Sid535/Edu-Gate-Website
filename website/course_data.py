# course_data.py file
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, current_app
from flask_sqlalchemy import SQLAlchemy

course_data = Blueprint('course_data', __name__)