from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app import app, db
from models import User
from forms import LoginForm, RegistrationForm, PasswordChangeForm
from utils import log_activity
from datetime import datetime

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login route"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            log_activity(f"User logged in: {user.username}", 
                         f"Login from IP: {request.remote_addr}", 
                         user.id)
            
            # Redirect to the page the user was trying to access
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('dashboard'))
        else:
            flash('Login failed. Check username and password.', 'danger')
    
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
@login_required
def logout():
    """User logout route"""
    log_activity(f"User logged out: {current_user.username}", 
                 f"Logout from IP: {request.remote_addr}", 
                 current_user.id)
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route - accessible only to admins"""
    # Redirect to admin user creation page if admin or to login if not
    if current_user.is_authenticated and current_user.is_admin():
        return redirect(url_for('admin_create_user'))
    else:
        flash('Only administrators can register new users.', 'warning')
        return redirect(url_for('login'))

@app.route('/profile', methods=['GET'])
@login_required
def profile():
    """User profile view"""
    return render_template('profile.html', title='Your Profile', user=current_user)

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Password change route"""
    form = PasswordChangeForm()
    
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            
            log_activity(
                f"Password changed for user: {current_user.username}",
                f"Password change from IP: {request.remote_addr}",
                current_user.id
            )
            
            flash('Your password has been changed successfully.', 'success')
            return redirect(url_for('profile'))
        else:
            flash('Current password is incorrect.', 'danger')
    
    return render_template('change_password.html', title='Change Password', form=form)
