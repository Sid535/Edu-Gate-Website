import os
from flask import Flask
from flask_login import LoginManager
from .database import db
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(24).hex())
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://{}:{}@{}/{}'.format(
        os.environ.get('DB_USER', 'root'),
        os.environ.get('DB_PASSWORD', '12082005'),
        os.environ.get('DB_HOST', 'localhost'),
        os.environ.get('DB_NAME', 'edugate')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

def create_app():
    app = Flask(__name__, template_folder="templates")
    
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    
    # Flask-Login setup
    login_manager = LoginManager()
    login_manager.login_view = "/login"
    login_manager.init_app(app)
    
    # Import models
    from .models import load_user
    login_manager.user_loader(load_user)

    # Register blueprints
    from .auth import auth
    from .views import views
    from .courses import courses_bp
    from .tests import tests_bp
    from .subjects import subjects_bp
    
    app.register_blueprint(auth)
    app.register_blueprint(views)
    app.register_blueprint(courses_bp, url_prefix='/courses')
    app.register_blueprint(tests_bp, url_prefix='/tests')
    app.register_blueprint(subjects_bp, url_prefix='/subjects')

    try:
        with app.app_context():
            db.create_all()
    except Exception as e:
        print(f"An error occurred while creating tables: {e}")

    return app
