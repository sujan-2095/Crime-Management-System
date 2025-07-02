from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import app, db
from models import Crime, Offender, Investigation, LegalProceeding, SystemLog
from forms import SearchForm
from utils import log_activity
from datetime import datetime

# Home page route
@app.route('/')
def index():
    """Landing page with system overview"""
    return render_template('index.html', title='Crime Record Management System')

# Dashboard route
@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard with summary and statistics"""
    # Count statistics for dashboard
    crime_count = Crime.query.count()
    offender_count = Offender.query.count()
    investigation_count = Investigation.query.count()
    legal_count = LegalProceeding.query.count()
    
    # Recent activities
    if current_user.is_admin():
        recent_crimes = Crime.query.order_by(Crime.date_reported.desc()).limit(5).all()
        recent_investigations = Investigation.query.order_by(Investigation.updated_at.desc()).limit(5).all()
    else:
        recent_crimes = Crime.query.filter_by(reported_by=current_user.id).order_by(Crime.date_reported.desc()).limit(5).all()
        recent_investigations = Investigation.query.filter_by(officer_id=current_user.id).order_by(Investigation.updated_at.desc()).limit(5).all()
    
    # Statistics for charts
    crime_by_type = db.session.query(Crime.type, db.func.count(Crime.id)).group_by(Crime.type).all()
    crime_by_status = db.session.query(Crime.status, db.func.count(Crime.id)).group_by(Crime.status).all()
    
    return render_template('dashboard.html', 
                          title='Dashboard',
                          crime_count=crime_count,
                          offender_count=offender_count,
                          investigation_count=investigation_count,
                          legal_count=legal_count,
                          recent_crimes=recent_crimes,
                          recent_investigations=recent_investigations,
                          crime_by_type=crime_by_type,
                          crime_by_status=crime_by_status)

# Search functionality
@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    """Search across different records"""
    form = SearchForm()
    results = []
    
    if form.validate_on_submit() or request.args.get('query'):
        query = form.query.data if form.validate_on_submit() else request.args.get('query')
        category = form.category.data if form.validate_on_submit() else request.args.get('category', 'crime')
        
        search_query = f"%{query}%"
        
        if category == 'crime':
            results = Crime.query.filter(
                (Crime.title.like(search_query)) | 
                (Crime.description.like(search_query)) | 
                (Crime.location.like(search_query))
            ).all()
        elif category == 'offender':
            results = Offender.query.filter(
                (Offender.name.like(search_query)) | 
                (Offender.address.like(search_query)) | 
                (Offender.identification.like(search_query))
            ).all()
        elif category == 'investigation':
            results = Investigation.query.filter(
                (Investigation.progress_notes.like(search_query)) | 
                (Investigation.findings.like(search_query))
            ).all()
        elif category == 'legal':
            results = LegalProceeding.query.filter(
                (LegalProceeding.case_number.like(search_query)) | 
                (LegalProceeding.court_name.like(search_query)) | 
                (LegalProceeding.judge.like(search_query)) | 
                (LegalProceeding.verdict.like(search_query))
            ).all()
            
        log_activity(f"Searched for {query} in {category} category", f"Query: {query}, Results: {len(results)}")
            
    return render_template('search.html', 
                           title='Search Records',
                           form=form,
                           results=results,
                           category=form.category.data if form.validate_on_submit() else request.args.get('category', 'crime'))

# 404 Error handler
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# 500 Error handler
@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
