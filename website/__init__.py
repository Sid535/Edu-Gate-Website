# __init__.py file
import os
from flask import Flask
from flask_login import LoginManager
from .database import db
from dotenv import load_dotenv

load_dotenv() 

def create_app():
    app = Flask(__name__, template_folder="templates")
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24).hex())
    
    # Database config
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://{}:{}@{}/{}'.format(
        os.environ.get('DB_USER', 'root'),
        os.environ.get('DB_PASSWORD', '12082005'),
        os.environ.get('DB_HOST', 'localhost'),
        os.environ.get('DB_NAME', 'edugate')
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    
    # Flask-Login setup
    login_manager = LoginManager()
    login_manager.login_view = "auth.login_page"  # Assuming blueprint prefix
    login_manager.init_app(app)
    
    # Import models AFTER initializing db
    from .models import load_user
    login_manager.user_loader(load_user)

    # Register blueprints
    from .auth import auth
    from .views import views
    from .course_data import course_data
    
    app.register_blueprint(auth)
    app.register_blueprint(views)
    app.register_blueprint(course_data, url_prefix='/courses')

    return app