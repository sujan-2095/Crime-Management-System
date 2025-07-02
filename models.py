from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Association table for many-to-many relationship between offenders and crimes
offender_crime = db.Table('offender_crime',
    db.Column('offender_id', db.Integer, db.ForeignKey('offender.id'), primary_key=True),
    db.Column('crime_id', db.Integer, db.ForeignKey('crime.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    """User model for authentication and role-based access"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='police')  # 'admin' or 'police'
    badge_number = db.Column(db.String(20), nullable=True)
    department = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    crimes = db.relationship('Crime', backref='reported_by_user', lazy=True)
    investigations = db.relationship('Investigation', backref='assigned_officer', lazy=True)
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Check if user has admin role"""
        return self.role == 'admin'
    
    def __repr__(self):
        return f'<User {self.username}>'

class Crime(db.Model):
    """Crime record model"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    date_occurred = db.Column(db.DateTime, nullable=False)
    date_reported = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='Open')  # Open, Under Investigation, Closed, Solved
    description = db.Column(db.Text, nullable=False)
    reported_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    offenders = db.relationship('Offender', secondary=offender_crime, 
                               backref=db.backref('crimes', lazy='dynamic'))
    investigations = db.relationship('Investigation', backref='crime', lazy=True)
    legal_proceedings = db.relationship('LegalProceeding', backref='crime', lazy=True)
    
    def __repr__(self):
        return f'<Crime {self.title}>'

class Offender(db.Model):
    """Offender profile model"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    dob = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    contact = db.Column(db.String(50), nullable=True)
    identification = db.Column(db.String(50), nullable=True)  # ID number, SSN, etc.
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Offender {self.name}>'

class Investigation(db.Model):
    """Investigation tracking model"""
    id = db.Column(db.Integer, primary_key=True)
    crime_id = db.Column(db.Integer, db.ForeignKey('crime.id'), nullable=False)
    officer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='Active')  # Active, Suspended, Completed
    progress_notes = db.Column(db.Text, nullable=True)
    findings = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Investigation {self.id} for Crime {self.crime_id}>'

class LegalProceeding(db.Model):
    """Legal case and proceedings model"""
    id = db.Column(db.Integer, primary_key=True)
    crime_id = db.Column(db.Integer, db.ForeignKey('crime.id'), nullable=False)
    case_number = db.Column(db.String(50), nullable=False)
    court_name = db.Column(db.String(100), nullable=False)
    judge = db.Column(db.String(100), nullable=True)
    prosecutor = db.Column(db.String(100), nullable=True)
    defense_attorney = db.Column(db.String(100), nullable=True)
    hearing_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='Pending')  # Pending, In Progress, Closed
    verdict = db.Column(db.String(50), nullable=True)
    sentence = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<LegalProceeding {self.case_number}>'

class SystemLog(db.Model):
    """System activity logging for audit purposes"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='logs')
    
    def __repr__(self):
        return f'<SystemLog {self.action} by User {self.user_id}>'
