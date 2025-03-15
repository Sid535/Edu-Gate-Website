import os
import mysql.connector
from mysql.connector import pooling
from flask import Flask
from flask_login import LoginManager, UserMixin
from .views import views

# Database connection pool
db_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="mypool",
    pool_size=5,
    host=os.environ.get('DB_HOST', 'localhost'),
    user=os.environ.get('DB_USER', 'root'),
    password=os.environ.get('DB_PASSWORD', '12082005'),
    database=os.environ.get('DB_NAME', 'edugate')
)

# Function to get database connection
def get_db_connection():
    return db_pool.get_connection()

def create_app():
    app = Flask(__name__, template_folder="templates")
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', '12082005')

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.login_view = "login_page"
    login_manager.init_app(app)

    # User class for Flask-Login
    class User(UserMixin):
        def __init__(self, id, name, email, username):
            self.id = id
            self.name = name
            self.email = email
            self.username = username

    # Flask-Login: Load user by ID
    @login_manager.user_loader
    def load_user(user_id):
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            return User(user["id"], user["name"], user["email"], user["username"])
        return None

    # Register blueprints
    app.register_blueprint(views, url_prefix='/')

    return app
