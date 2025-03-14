from flask import get_db_connection, Blueprint,Flask

def create_app():
    app = Flask(__name__, template_folder="website/templates")
    app.config['SECRET_KEY'] = '12082005'
    
    from .views import views
    
    app.register_blueprint(views, url_prefix='/')
    
    return app