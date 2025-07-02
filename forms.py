from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SelectField, DateTimeField, DateField, Field
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional
from models import User
from datetime import datetime

# Let's revert back to using standard DateTimeField but with format conversion
# We'll fix the issue by reverting to the standard fields but adding processing capability

class FlexibleDateTimeField(DateTimeField):
    """Custom DateTimeField that accepts various datetime formats"""
    
    def process_formdata(self, valuelist):
        if not valuelist or not valuelist[0]:
            self.data = None
            return
            
        date_str = valuelist[0]
        
        # Try multiple formats
        formats = [
            '%Y-%m-%dT%H:%M',  # HTML5 datetime-local
            '%Y-%m-%d %H:%M',  # Standard format
            '%m/%d/%Y %H:%M',  # US format
            '%d/%m/%Y %H:%M',  # European format
        ]
        
        # Also try formats with seconds
        formats_with_seconds = [f + ':%S' for f in formats]
        formats.extend(formats_with_seconds)
        
        # Replace 'T' with space if present
        if 'T' in date_str:
            date_str = date_str.replace('T', ' ')
        
        for format_str in formats:
            try:
                self.data = datetime.strptime(date_str, format_str)
                return
            except ValueError:
                continue
        
        # If we couldn't parse with any of our formats, let the parent class try
        try:
            super().process_formdata(valuelist)
        except ValueError:
            # If the parent class also fails, raise a more helpful error
            self.data = None
            raise ValueError(f"Invalid date format. Please use YYYY-MM-DD HH:MM format. Got: {date_str}")

class LoginForm(FlaskForm):
    """User login form"""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')

class RegistrationForm(FlaskForm):
    """User registration form"""
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    badge_number = StringField('Badge Number', validators=[DataRequired(), Length(min=2, max=20)])
    department = StringField('Department', validators=[DataRequired(), Length(min=2, max=100)])
    password = PasswordField('Password', validators=[
        DataRequired(), 
        Length(min=8, message='Password must be at least 8 characters')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), 
        EqualTo('password', message='Passwords must match')
    ])
    role = SelectField('Role', choices=[('police', 'Police Officer'), ('admin', 'Admin')], default='police')
    
    def validate_username(self, username):
        """Validate username is unique"""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists. Please choose a different one.')
    
    def validate_email(self, email):
        """Validate email is unique"""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already exists. Please use a different one.')

class UserEditForm(FlaskForm):
    """Form for editing user details"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    badge_number = StringField('Badge Number', validators=[DataRequired(), Length(min=2, max=20)])
    department = StringField('Department', validators=[DataRequired(), Length(min=2, max=100)])
    role = SelectField('Role', choices=[('police', 'Police Officer'), ('admin', 'Admin')])
    
class PasswordChangeForm(FlaskForm):
    """Form for changing password"""
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(), 
        Length(min=8, message='Password must be at least 8 characters')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(), 
        EqualTo('new_password', message='Passwords must match')
    ])

class CrimeForm(FlaskForm):
    """Form for crime records"""
    title = StringField('Crime Title', validators=[DataRequired(), Length(max=100)])
    type = SelectField('Crime Type', choices=[
        ('theft', 'Theft'),
        ('assault', 'Assault'),
        ('burglary', 'Burglary'),
        ('robbery', 'Robbery'),
        ('homicide', 'Homicide'),
        ('fraud', 'Fraud'),
        ('vandalism', 'Vandalism'),
        ('drug_offense', 'Drug Offense'),
        ('cybercrime', 'Cybercrime'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired(), Length(max=200)])
    date_occurred = FlexibleDateTimeField('Date Occurred', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('Open', 'Open'),
        ('Under Investigation', 'Under Investigation'),
        ('Closed', 'Closed'),
        ('Solved', 'Solved')
    ], validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])

class OffenderForm(FlaskForm):
    """Form for offender profiles"""
    name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    dob = DateField('Date of Birth', format='%Y-%m-%d', validators=[Optional()])
    gender = SelectField('Gender', choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('', 'Not Specified')
    ])
    address = StringField('Address', validators=[Optional(), Length(max=200)])
    contact = StringField('Contact', validators=[Optional(), Length(max=50)])
    identification = StringField('Identification Number', validators=[Optional(), Length(max=50)])
    description = TextAreaField('Description', validators=[Optional()])

class InvestigationForm(FlaskForm):
    """Form for investigation tracking"""
    crime_id = SelectField('Crime', coerce=int, validators=[DataRequired()])
    officer_id = SelectField('Assigned Officer', coerce=int, validators=[DataRequired()])
    start_date = FlexibleDateTimeField('Start Date', format='%Y-%m-%dT%H:%M', default=datetime.now, validators=[DataRequired()])
    end_date = FlexibleDateTimeField('End Date', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    status = SelectField('Status', choices=[
        ('Active', 'Active'),
        ('Suspended', 'Suspended'),
        ('Completed', 'Completed')
    ], validators=[DataRequired()])
    progress_notes = TextAreaField('Progress Notes', validators=[Optional()])
    findings = TextAreaField('Findings', validators=[Optional()])

class LegalProceedingForm(FlaskForm):
    """Form for legal proceedings"""
    crime_id = SelectField('Crime', coerce=int, validators=[DataRequired()])
    case_number = StringField('Case Number', validators=[DataRequired(), Length(max=50)])
    court_name = StringField('Court Name', validators=[DataRequired(), Length(max=100)])
    judge = StringField('Judge', validators=[Optional(), Length(max=100)])
    prosecutor = StringField('Prosecutor', validators=[Optional(), Length(max=100)])
    defense_attorney = StringField('Defense Attorney', validators=[Optional(), Length(max=100)])
    hearing_date = FlexibleDateTimeField('Hearing Date', format='%Y-%m-%dT%H:%M', validators=[Optional()])
    status = SelectField('Status', choices=[
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Closed', 'Closed')
    ], validators=[DataRequired()])
    verdict = StringField('Verdict', validators=[Optional(), Length(max=50)])
    sentence = TextAreaField('Sentence', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])

class SearchForm(FlaskForm):
    """Form for searching records"""
    query = StringField('Search', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('crime', 'Crime'),
        ('offender', 'Offender'),
        ('investigation', 'Investigation'),
        ('legal', 'Legal Proceeding')
    ], default='crime')
