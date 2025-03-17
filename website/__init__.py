import os
from flask import Flask
from flask_login import LoginManager
# Register blueprints
from .database import db
from .auth import auth
from .views import views
from .course_data import course_data
from .models import load_user, User

def create_app():
    app = Flask(__name__, template_folder="templates")
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24).hex())
    
    # Database configuration for SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://{}:{}@{}/{}'.format(
        os.environ.get('DB_USER', 'root'),
        os.environ.get('DB_PASSWORD', '12082005'),
        os.environ.get('DB_HOST', 'localhost'),
        os.environ.get('DB_NAME', 'edugate')
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize SQLAlchemy
    db.init_app(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = "login_page"
    login_manager.init_app(app)
    
    # Set the user loader function
    login_manager.user_loader(load_user)

    # Register blueprints
    from .auth import auth
    from .views import views
    from .course_data import course_data
    from .models import model
    app.register_blueprint(auth, url_prefix='/')

    app.register_blueprint(views, url_prefix='/')
    
    app.register_blueprint(course_data, url_prefix='/')
    
    app.register_blueprint(model, url_prefix='/')
    
    @app.context_processor
    def inject_user(): # noqa: F401
        from flask_login import current_user
        return dict(current_user=current_user)

    return app