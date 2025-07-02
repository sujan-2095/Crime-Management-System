from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import app, db
from models import User, SystemLog, Crime, Investigation, LegalProceeding
from forms import UserEditForm, RegistrationForm
from utils import log_activity, admin_required
from datetime import datetime, timedelta
import json

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    """Admin route to manage users"""
    users = User.query.all()
    return render_template('admin/users.html', 
                           title='User Management',
                           users=users)

@app.route('/admin/create_user', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_create_user():
    """Admin route to create new users"""
    form = RegistrationForm()
    
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            badge_number=form.badge_number.data,
            department=form.department.data,
            role=form.role.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        log_activity(
            f"Admin created new user: {user.username}",
            f"User created with role: {user.role}, by admin: {current_user.username}",
            current_user.id
        )
        
        flash(f'User {user.username} created successfully!', 'success')
        return redirect(url_for('admin_users'))
    
    return render_template('admin/create_user.html', 
                           title='Create New User',
                           form=form)

@app.route('/admin/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_user(user_id):
    """Admin route to edit users"""
    user = User.query.get_or_404(user_id)
    form = UserEditForm()
    
    if request.method == 'GET':
        form.email.data = user.email
        form.full_name.data = user.full_name
        form.badge_number.data = user.badge_number
        form.department.data = user.department
        form.role.data = user.role
    
    if form.validate_on_submit():
        user.email = form.email.data
        user.full_name = form.full_name.data
        user.badge_number = form.badge_number.data
        user.department = form.department.data
        user.role = form.role.data
        
        db.session.commit()
        
        log_activity(
            f"Admin updated user: {user.username}",
            f"User details updated by admin: {current_user.username}",
            current_user.id
        )
        
        flash(f'User {user.username} updated successfully!', 'success')
        return redirect(url_for('admin_users'))
    
    return render_template('admin/edit_user.html', 
                           title='Edit User',
                           form=form,
                           user=user)

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    """Admin route to delete users"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot delete your own account!', 'danger')
        return redirect(url_for('admin_users'))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    log_activity(
        f"Admin deleted user: {username}",
        f"User deleted by admin: {current_user.username}",
        current_user.id
    )
    
    flash(f'User {username} has been deleted.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/logs')
@login_required
@admin_required
def admin_logs():
    """Admin route to view system logs"""
    page = request.args.get('page', 1, type=int)
    logs = SystemLog.query.order_by(SystemLog.timestamp.desc()).paginate(
        page=page, per_page=20, error_out=False)
    
    return render_template('admin/logs.html', 
                           title='System Logs',
                           logs=logs)

@app.route('/admin/reports')
@login_required
@admin_required
def admin_reports():
    """Admin route for reports and analytics"""
    # Time period for reports
    period = request.args.get('period', 'month')
    
    if period == 'week':
        start_date = datetime.now() - timedelta(days=7)
    elif period == 'month':
        start_date = datetime.now() - timedelta(days=30)
    elif period == 'year':
        start_date = datetime.now() - timedelta(days=365)
    else:
        start_date = datetime.now() - timedelta(days=30)  # Default to month
    
    # Crime statistics
    crimes_by_type = db.session.query(
        Crime.type, db.func.count(Crime.id)
    ).group_by(Crime.type).all()
    
    crimes_by_status = db.session.query(
        Crime.status, db.func.count(Crime.id)
    ).group_by(Crime.status).all()
    
    crimes_over_time = db.session.query(
        db.func.date(Crime.date_reported), db.func.count(Crime.id)
    ).group_by(db.func.date(Crime.date_reported)
    ).filter(Crime.date_reported >= start_date).all()
    
    # Investigation statistics
    investigations_by_status = db.session.query(
        Investigation.status, db.func.count(Investigation.id)
    ).group_by(Investigation.status).all()
    
    # Legal proceedings statistics
    legal_by_status = db.session.query(
        LegalProceeding.status, db.func.count(LegalProceeding.id)
    ).group_by(LegalProceeding.status).all()
    
    # Officer performance
    officer_case_counts = db.session.query(
        User.full_name, db.func.count(Investigation.id)
    ).join(Investigation, User.id == Investigation.officer_id
    ).group_by(User.id).all()
    
    # Convert data for charts
    crimes_by_type_data = {
        'labels': [t[0] for t in crimes_by_type],
        'values': [t[1] for t in crimes_by_type]
    }
    
    crimes_by_status_data = {
        'labels': [s[0] for s in crimes_by_status],
        'values': [s[1] for s in crimes_by_status]
    }
    
    crimes_over_time_data = {
        'labels': [str(t[0]) for t in crimes_over_time],
        'values': [t[1] for t in crimes_over_time]
    }
    
    investigations_by_status_data = {
        'labels': [s[0] for s in investigations_by_status],
        'values': [s[1] for s in investigations_by_status]
    }
    
    legal_by_status_data = {
        'labels': [s[0] for s in legal_by_status],
        'values': [s[1] for s in legal_by_status]
    }
    
    officer_performance_data = {
        'labels': [o[0] for o in officer_case_counts],
        'values': [o[1] for o in officer_case_counts]
    }
    
    return render_template('admin/reports.html',
                           title='Reports & Analytics',
                           period=period,
                           crimes_by_type=json.dumps(crimes_by_type_data),
                           crimes_by_status=json.dumps(crimes_by_status_data),
                           crimes_over_time=json.dumps(crimes_over_time_data),
                           investigations_by_status=json.dumps(investigations_by_status_data),
                           legal_by_status=json.dumps(legal_by_status_data),
                           officer_performance=json.dumps(officer_performance_data))
