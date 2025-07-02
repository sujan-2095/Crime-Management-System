from flask import abort
from flask_login import current_user
from functools import wraps
from app import db
from models import SystemLog
import datetime
import re

def log_activity(action, details=None, user_id=None, ip_address=None):
    """
    Log system activities for audit purposes
    """
    if user_id is None and current_user.is_authenticated:
        user_id = current_user.id
        
    log = SystemLog(
        user_id=user_id,
        action=action,
        details=details,
        ip_address=ip_address
    )
    
    db.session.add(log)
    db.session.commit()

def admin_required(f):
    """
    Decorator to ensure only admin users can access a route
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function

def format_date(date):
    """
    Format datetime objects for display
    """
    if date:
        return date.strftime('%Y-%m-%d %H:%M')
    return ""

def format_date_short(date):
    """
    Format date objects for display (short version)
    """
    if date:
        return date.strftime('%Y-%m-%d')
    return ""

def sanitize_input(text):
    """
    Sanitize user input to prevent XSS attacks
    """
    if not text:
        return text
    
    # Remove HTML tags
    text = re.sub(r'<[^>]*>', '', text)
    
    # Replace special characters
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&#x27;')
    
    return text

def calculate_age(dob):
    """
    Calculate age from date of birth
    """
    if not dob:
        return None
    
    today = datetime.date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

def get_status_badge_color(status):
    """
    Return Bootstrap badge color class based on status
    """
    status_colors = {
        # Crime statuses
        'Open': 'danger',
        'Under Investigation': 'warning',
        'Closed': 'secondary',
        'Solved': 'success',
        
        # Investigation statuses
        'Active': 'primary',
        'Suspended': 'warning',
        'Completed': 'success',
        
        # Legal proceeding statuses
        'Pending': 'info',
        'In Progress': 'primary',
        'Closed': 'secondary'
    }
    
    return status_colors.get(status, 'secondary')
