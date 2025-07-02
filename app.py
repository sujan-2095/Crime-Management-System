import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-key-for-testing")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///crms.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the app with the extension
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Import routes after initializing db to avoid circular imports
with app.app_context():
    # Import models to ensure tables are created
    from models import User, Crime, Offender, Investigation, LegalProceeding, SystemLog
    from werkzeug.security import generate_password_hash
    
    # Create database tables
    db.create_all()
    
    # Create default admin user if no users exist
    if User.query.count() == 0:
        default_admin = User(
            username="admin",
            email="admin@example.com",
            full_name="System Administrator",
            badge_number="ADMIN-001",
            department="System Administration",
            role="admin",
            password_hash=generate_password_hash("admin123")
        )
        db.session.add(default_admin)
        db.session.commit()
        print("Default admin user created. Username: admin, Password: admin123")
    
    # Import and register routes
    from routes import *
    from auth import *
    from admin import *
    from officer import *
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register utility functions with the template context
    from utils import calculate_age, format_date, format_date_short, get_status_badge_color
    
    @app.context_processor
    def utility_functions():
        return {
            'calculate_age': calculate_age,
            'format_date': format_date,
            'format_date_short': format_date_short,
            'get_status_badge_color': get_status_badge_color
        }
