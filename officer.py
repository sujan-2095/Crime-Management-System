from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import app, db
from models import Crime, Offender, Investigation, LegalProceeding, User, offender_crime
from forms import CrimeForm, OffenderForm, InvestigationForm, LegalProceedingForm
from utils import log_activity
from datetime import datetime

# Crime management routes

@app.route('/crimes')
@login_required
def crimes_list():
    """List all crimes with filtering options"""
    # Get filter parameters
    status = request.args.get('status', '')
    type = request.args.get('type', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    # Start with the base query
    query = Crime.query
    
    # Apply filters if they exist
    if status:
        query = query.filter(Crime.status == status)
    
    if type:
        query = query.filter(Crime.type == type)
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Crime.date_occurred >= from_date)
        except ValueError:
            flash('Invalid date format for From Date', 'warning')
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d')
            query = query.filter(Crime.date_occurred <= to_date)
        except ValueError:
            flash('Invalid date format for To Date', 'warning')
    
    # If not admin, show only crimes reported by the current user
    if not current_user.is_admin():
        query = query.filter(Crime.reported_by == current_user.id)
    
    # Execute query with pagination
    page = request.args.get('page', 1, type=int)
    crimes = query.order_by(Crime.date_reported.desc()).paginate(
        page=page, per_page=10, error_out=False)
    
    # Get unique values for filter dropdowns
    statuses = db.session.query(Crime.status).distinct().all()
    types = db.session.query(Crime.type).distinct().all()
    
    return render_template('crimes/list.html',
                          title='Crime Records',
                          crimes=crimes,
                          statuses=[s[0] for s in statuses],
                          types=[t[0] for t in types],
                          current_status=status,
                          current_type=type,
                          date_from=date_from,
                          date_to=date_to)

@app.route('/crimes/create', methods=['GET', 'POST'])
@login_required
def crime_create():
    """Create a new crime record"""
    form = CrimeForm()
    
    if form.validate_on_submit():
        try:
            crime = Crime(
                title=form.title.data,
                type=form.type.data,
                location=form.location.data,
                date_occurred=form.date_occurred.data,
                status=form.status.data,
                description=form.description.data,
                reported_by=current_user.id
            )
            
            db.session.add(crime)
            db.session.commit()
            
            log_activity(
                f"Crime record created: {crime.title}",
                f"Crime ID: {crime.id}, Type: {crime.type}, Status: {crime.status}",
                current_user.id
            )
            
            flash('Crime record has been created successfully.', 'success')
            return redirect(url_for('crimes_list'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error creating crime record: {str(e)}")
            flash(f'Error creating crime record: {str(e)}', 'danger')
    elif request.method == 'POST':
        app.logger.debug(f"Form validation failed. Errors: {form.errors}")
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", "danger")
    
    return render_template('crimes/create.html',
                          title='Create Crime Record',
                          form=form)

@app.route('/crimes/view/<int:crime_id>')
@login_required
def crime_view(crime_id):
    """View crime details"""
    crime = Crime.query.get_or_404(crime_id)
    
    # Check if user has permission to view this crime
    if not current_user.is_admin() and crime.reported_by != current_user.id:
        abort(403)
    
    # Get related data
    offenders = crime.offenders
    investigations = Investigation.query.filter_by(crime_id=crime.id).all()
    legal_proceedings = LegalProceeding.query.filter_by(crime_id=crime.id).all()
    reporter = User.query.get(crime.reported_by)
    
    return render_template('crimes/view.html',
                          title=f'Crime: {crime.title}',
                          crime=crime,
                          offenders=offenders,
                          investigations=investigations,
                          legal_proceedings=legal_proceedings,
                          reporter=reporter)

@app.route('/crimes/edit/<int:crime_id>', methods=['GET', 'POST'])
@login_required
def crime_edit(crime_id):
    """Edit crime record"""
    crime = Crime.query.get_or_404(crime_id)
    
    # Check if user has permission to edit this crime
    if not current_user.is_admin() and crime.reported_by != current_user.id:
        abort(403)
    
    form = CrimeForm()
    
    if request.method == 'GET':
        form.title.data = crime.title
        form.type.data = crime.type
        form.location.data = crime.location
        form.date_occurred.data = crime.date_occurred
        form.status.data = crime.status
        form.description.data = crime.description
    
    if form.validate_on_submit():
        crime.title = form.title.data
        crime.type = form.type.data
        crime.location = form.location.data
        crime.date_occurred = form.date_occurred.data
        crime.status = form.status.data
        crime.description = form.description.data
        
        db.session.commit()
        
        log_activity(
            f"Crime record updated: {crime.title}",
            f"Crime ID: {crime.id}, Type: {crime.type}, Status: {crime.status}",
            current_user.id
        )
        
        flash('Crime record has been updated successfully.', 'success')
        return redirect(url_for('crime_view', crime_id=crime.id))
    
    return render_template('crimes/edit.html',
                          title=f'Edit Crime: {crime.title}',
                          form=form,
                          crime=crime)

@app.route('/crimes/delete/<int:crime_id>', methods=['POST'])
@login_required
def crime_delete(crime_id):
    """Delete crime record"""
    crime = Crime.query.get_or_404(crime_id)
    
    # Check if user has permission to delete this crime
    if not current_user.is_admin() and crime.reported_by != current_user.id:
        abort(403)
    
    title = crime.title
    db.session.delete(crime)
    db.session.commit()
    
    log_activity(
        f"Crime record deleted: {title}",
        f"Crime ID: {crime_id}",
        current_user.id
    )
    
    flash('Crime record has been deleted.', 'success')
    return redirect(url_for('crimes_list'))

# Offender management routes

@app.route('/offenders')
@login_required
def offenders_list():
    """List all offenders with filtering options"""
    # Get filter parameters
    gender = request.args.get('gender', '')
    name = request.args.get('name', '')
    
    # Start with the base query
    query = Offender.query
    
    # Apply filters if they exist
    if gender:
        query = query.filter(Offender.gender == gender)
    
    if name:
        query = query.filter(Offender.name.ilike(f'%{name}%'))
    
    # Execute query with pagination
    page = request.args.get('page', 1, type=int)
    offenders = query.order_by(Offender.name).paginate(
        page=page, per_page=10, error_out=False)
    
    # Get unique values for filter dropdowns
    genders = db.session.query(Offender.gender).distinct().all()
    
    return render_template('offenders/list.html',
                          title='Offender Profiles',
                          offenders=offenders,
                          genders=[g[0] for g in genders if g[0]],
                          current_gender=gender,
                          current_name=name)

@app.route('/offenders/create', methods=['GET', 'POST'])
@login_required
def offender_create():
    """Create a new offender profile"""
    form = OffenderForm()
    
    # Get crime ID from query parameter if linking to a crime
    crime_id = request.args.get('crime_id')
    
    if form.validate_on_submit():
        offender = Offender(
            name=form.name.data,
            dob=form.dob.data,
            gender=form.gender.data,
            address=form.address.data,
            contact=form.contact.data,
            identification=form.identification.data,
            description=form.description.data
        )
        
        db.session.add(offender)
        
        # If crime_id is provided, link the offender to the crime
        if crime_id:
            crime = Crime.query.get(crime_id)
            if crime:
                offender.crimes.append(crime)
        
        db.session.commit()
        
        log_activity(
            f"Offender profile created: {offender.name}",
            f"Offender ID: {offender.id}",
            current_user.id
        )
        
        flash('Offender profile has been created successfully.', 'success')
        
        # Redirect back to crime view if linked to a crime
        if crime_id:
            return redirect(url_for('crime_view', crime_id=crime_id))
        else:
            return redirect(url_for('offenders_list'))
    
    return render_template('offenders/create.html',
                          title='Create Offender Profile',
                          form=form,
                          crime_id=crime_id)

@app.route('/offenders/view/<int:offender_id>')
@login_required
def offender_view(offender_id):
    """View offender details"""
    offender = Offender.query.get_or_404(offender_id)
    crimes = offender.crimes.all()
    
    return render_template('offenders/view.html',
                          title=f'Offender: {offender.name}',
                          offender=offender,
                          crimes=crimes)

@app.route('/offenders/edit/<int:offender_id>', methods=['GET', 'POST'])
@login_required
def offender_edit(offender_id):
    """Edit offender profile"""
    offender = Offender.query.get_or_404(offender_id)
    form = OffenderForm()
    
    if request.method == 'GET':
        form.name.data = offender.name
        form.dob.data = offender.dob
        form.gender.data = offender.gender
        form.address.data = offender.address
        form.contact.data = offender.contact
        form.identification.data = offender.identification
        form.description.data = offender.description
    
    if form.validate_on_submit():
        offender.name = form.name.data
        offender.dob = form.dob.data
        offender.gender = form.gender.data
        offender.address = form.address.data
        offender.contact = form.contact.data
        offender.identification = form.identification.data
        offender.description = form.description.data
        
        db.session.commit()
        
        log_activity(
            f"Offender profile updated: {offender.name}",
            f"Offender ID: {offender.id}",
            current_user.id
        )
        
        flash('Offender profile has been updated successfully.', 'success')
        return redirect(url_for('offender_view', offender_id=offender.id))
    
    return render_template('offenders/edit.html',
                          title=f'Edit Offender: {offender.name}',
                          form=form,
                          offender=offender)

@app.route('/offenders/delete/<int:offender_id>', methods=['POST'])
@login_required
def offender_delete(offender_id):
    """Delete offender profile"""
    offender = Offender.query.get_or_404(offender_id)
    
    name = offender.name
    db.session.delete(offender)
    db.session.commit()
    
    log_activity(
        f"Offender profile deleted: {name}",
        f"Offender ID: {offender_id}",
        current_user.id
    )
    
    flash('Offender profile has been deleted.', 'success')
    return redirect(url_for('offenders_list'))

@app.route('/link_offender_to_crime', methods=['POST'])
@login_required
def link_offender_to_crime():
    """Link an existing offender to a crime"""
    crime_id = request.form.get('crime_id', type=int)
    offender_id = request.form.get('offender_id', type=int)
    
    if not crime_id or not offender_id:
        flash('Missing crime ID or offender ID.', 'danger')
        return redirect(url_for('crimes_list'))
    
    crime = Crime.query.get_or_404(crime_id)
    offender = Offender.query.get_or_404(offender_id)
    
    # Check if user has permission
    if not current_user.is_admin() and crime.reported_by != current_user.id:
        abort(403)
    
    # Check if already linked
    if offender in crime.offenders:
        flash(f'Offender {offender.name} is already linked to this crime.', 'info')
    else:
        crime.offenders.append(offender)
        db.session.commit()
        
        log_activity(
            f"Offender linked to crime",
            f"Crime ID: {crime.id}, Offender ID: {offender.id}",
            current_user.id
        )
        
        flash(f'Offender {offender.name} has been linked to the crime.', 'success')
    
    return redirect(url_for('crime_view', crime_id=crime_id))

@app.route('/unlink_offender_from_crime', methods=['POST'])
@login_required
def unlink_offender_from_crime():
    """Unlink an offender from a crime"""
    crime_id = request.form.get('crime_id', type=int)
    offender_id = request.form.get('offender_id', type=int)
    
    if not crime_id or not offender_id:
        flash('Missing crime ID or offender ID.', 'danger')
        return redirect(url_for('crimes_list'))
    
    crime = Crime.query.get_or_404(crime_id)
    offender = Offender.query.get_or_404(offender_id)
    
    # Check if user has permission
    if not current_user.is_admin() and crime.reported_by != current_user.id:
        abort(403)
    
    # Remove the link
    if offender in crime.offenders:
        crime.offenders.remove(offender)
        db.session.commit()
        
        log_activity(
            f"Offender unlinked from crime",
            f"Crime ID: {crime.id}, Offender ID: {offender.id}",
            current_user.id
        )
        
        flash(f'Offender {offender.name} has been unlinked from the crime.', 'success')
    else:
        flash(f'Offender {offender.name} is not linked to this crime.', 'warning')
    
    return redirect(url_for('crime_view', crime_id=crime_id))

# Investigation management routes

@app.route('/investigations')
@login_required
def investigations_list():
    """List all investigations with filtering options"""
    # Get filter parameters
    status = request.args.get('status', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    # Start with the base query
    query = Investigation.query
    
    # Apply filters if they exist
    if status:
        query = query.filter(Investigation.status == status)
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Investigation.start_date >= from_date)
        except ValueError:
            flash('Invalid date format for From Date', 'warning')
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d')
            query = query.filter(Investigation.start_date <= to_date)
        except ValueError:
            flash('Invalid date format for To Date', 'warning')
    
    # If not admin, show only investigations assigned to the current user
    if not current_user.is_admin():
        query = query.filter(Investigation.officer_id == current_user.id)
    
    # Execute query with pagination
    page = request.args.get('page', 1, type=int)
    investigations = query.order_by(Investigation.updated_at.desc()).paginate(
        page=page, per_page=10, error_out=False)
    
    # Get unique values for filter dropdowns
    statuses = db.session.query(Investigation.status).distinct().all()
    
    return render_template('investigations/list.html',
                          title='Investigation Tracking',
                          investigations=investigations,
                          statuses=[s[0] for s in statuses],
                          current_status=status,
                          date_from=date_from,
                          date_to=date_to)

@app.route('/investigations/create', methods=['GET', 'POST'])
@login_required
def investigation_create():
    """Create a new investigation"""
    form = InvestigationForm()
    
    # Populate crime dropdown
    if current_user.is_admin():
        form.crime_id.choices = [(c.id, c.title) for c in Crime.query.all()]
    else:
        form.crime_id.choices = [(c.id, c.title) for c in Crime.query.filter_by(reported_by=current_user.id).all()]
    
    # Populate officer dropdown
    form.officer_id.choices = [(o.id, o.full_name) for o in User.query.filter_by(role='police').all()]
    
    # Get crime ID from query parameter if linking to a crime
    crime_id = request.args.get('crime_id')
    if crime_id:
        form.crime_id.data = int(crime_id)
    
    if form.validate_on_submit():
        investigation = Investigation(
            crime_id=form.crime_id.data,
            officer_id=form.officer_id.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            status=form.status.data,
            progress_notes=form.progress_notes.data,
            findings=form.findings.data
        )
        
        db.session.add(investigation)
        db.session.commit()
        
        # Update crime status to "Under Investigation"
        crime = Crime.query.get(form.crime_id.data)
        if crime and crime.status == 'Open':
            crime.status = 'Under Investigation'
            db.session.commit()
        
        log_activity(
            f"Investigation created for crime ID: {investigation.crime_id}",
            f"Investigation ID: {investigation.id}, Status: {investigation.status}, Assigned to: {investigation.officer_id}",
            current_user.id
        )
        
        flash('Investigation has been created successfully.', 'success')
        
        # Redirect back to crime view if linked to a crime
        if crime_id:
            return redirect(url_for('crime_view', crime_id=crime_id))
        else:
            return redirect(url_for('investigations_list'))
    
    return render_template('investigations/create.html',
                          title='Create Investigation',
                          form=form,
                          crime_id=crime_id)

@app.route('/investigations/view/<int:investigation_id>')
@login_required
def investigation_view(investigation_id):
    """View investigation details"""
    investigation = Investigation.query.get_or_404(investigation_id)
    
    # Check if user has permission to view this investigation
    if not current_user.is_admin() and investigation.officer_id != current_user.id:
        abort(403)
    
    crime = Crime.query.get(investigation.crime_id)
    officer = User.query.get(investigation.officer_id)
    
    return render_template('investigations/view.html',
                          title=f'Investigation for Crime: {crime.title}',
                          investigation=investigation,
                          crime=crime,
                          officer=officer)

@app.route('/investigations/edit/<int:investigation_id>', methods=['GET', 'POST'])
@login_required
def investigation_edit(investigation_id):
    """Edit investigation"""
    investigation = Investigation.query.get_or_404(investigation_id)
    
    # Check if user has permission to edit this investigation
    if not current_user.is_admin() and investigation.officer_id != current_user.id:
        abort(403)
    
    form = InvestigationForm()
    
    # Populate crime dropdown
    if current_user.is_admin():
        form.crime_id.choices = [(c.id, c.title) for c in Crime.query.all()]
    else:
        form.crime_id.choices = [(c.id, c.title) for c in Crime.query.filter_by(reported_by=current_user.id).all()]
    
    # Populate officer dropdown
    form.officer_id.choices = [(o.id, o.full_name) for o in User.query.filter_by(role='police').all()]
    
    if request.method == 'GET':
        form.crime_id.data = investigation.crime_id
        form.officer_id.data = investigation.officer_id
        form.start_date.data = investigation.start_date
        form.end_date.data = investigation.end_date
        form.status.data = investigation.status
        form.progress_notes.data = investigation.progress_notes
        form.findings.data = investigation.findings
    
    if form.validate_on_submit():
        # Store the old status for comparison
        old_status = investigation.status
        
        investigation.crime_id = form.crime_id.data
        investigation.officer_id = form.officer_id.data
        investigation.start_date = form.start_date.data
        investigation.end_date = form.end_date.data
        investigation.status = form.status.data
        investigation.progress_notes = form.progress_notes.data
        investigation.findings = form.findings.data
        
        # Update crime status if investigation is completed
        if old_status != 'Completed' and form.status.data == 'Completed':
            crime = Crime.query.get(investigation.crime_id)
            if crime:
                # Check if this is the only investigation for this crime
                other_investigations = Investigation.query.filter(
                    Investigation.crime_id == crime.id,
                    Investigation.id != investigation.id,
                    Investigation.status != 'Completed'
                ).count()
                
                if other_investigations == 0:
                    crime.status = 'Solved'
                    db.session.commit()
        
        db.session.commit()
        
        log_activity(
            f"Investigation updated for crime ID: {investigation.crime_id}",
            f"Investigation ID: {investigation.id}, Status: {investigation.status}",
            current_user.id
        )
        
        flash('Investigation has been updated successfully.', 'success')
        return redirect(url_for('investigation_view', investigation_id=investigation.id))
    
    return render_template('investigations/edit.html',
                          title='Edit Investigation',
                          form=form,
                          investigation=investigation)

@app.route('/investigations/delete/<int:investigation_id>', methods=['POST'])
@login_required
def investigation_delete(investigation_id):
    """Delete investigation"""
    investigation = Investigation.query.get_or_404(investigation_id)
    
    # Check if user has permission to delete this investigation
    if not current_user.is_admin() and investigation.officer_id != current_user.id:
        abort(403)
    
    crime_id = investigation.crime_id
    db.session.delete(investigation)
    db.session.commit()
    
    log_activity(
        f"Investigation deleted for crime ID: {crime_id}",
        f"Investigation ID: {investigation_id}",
        current_user.id
    )
    
    flash('Investigation has been deleted.', 'success')
    return redirect(url_for('investigations_list'))

# Legal Proceedings routes

@app.route('/legal')
@login_required
def legal_list():
    """List all legal proceedings with filtering options"""
    # Get filter parameters
    status = request.args.get('status', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    # Start with the base query
    query = LegalProceeding.query
    
    # Apply filters if they exist
    if status:
        query = query.filter(LegalProceeding.status == status)
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(LegalProceeding.hearing_date >= from_date)
        except ValueError:
            flash('Invalid date format for From Date', 'warning')
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d')
            query = query.filter(LegalProceeding.hearing_date <= to_date)
        except ValueError:
            flash('Invalid date format for To Date', 'warning')
    
    # If not admin, show only legal proceedings related to crimes reported by the current user
    if not current_user.is_admin():
        # Get crimes reported by current user
        user_crimes = db.session.query(Crime.id).filter_by(reported_by=current_user.id).all()
        user_crime_ids = [c[0] for c in user_crimes]
        
        query = query.filter(LegalProceeding.crime_id.in_(user_crime_ids))
    
    # Execute query with pagination
    page = request.args.get('page', 1, type=int)
    legal_proceedings = query.order_by(LegalProceeding.updated_at.desc()).paginate(
        page=page, per_page=10, error_out=False)
    
    # Get unique values for filter dropdowns
    statuses = db.session.query(LegalProceeding.status).distinct().all()
    
    return render_template('legal/list.html',
                          title='Legal Proceedings',
                          legal_proceedings=legal_proceedings,
                          statuses=[s[0] for s in statuses],
                          current_status=status,
                          date_from=date_from,
                          date_to=date_to)

@app.route('/legal/create', methods=['GET', 'POST'])
@login_required
def legal_create():
    """Create a new legal proceeding"""
    form = LegalProceedingForm()
    
    # Populate crime dropdown
    if current_user.is_admin():
        form.crime_id.choices = [(c.id, c.title) for c in Crime.query.all()]
    else:
        form.crime_id.choices = [(c.id, c.title) for c in Crime.query.filter_by(reported_by=current_user.id).all()]
    
    # Get crime ID from query parameter if linking to a crime
    crime_id = request.args.get('crime_id')
    if crime_id:
        form.crime_id.data = int(crime_id)
    
    if form.validate_on_submit():
        legal_proceeding = LegalProceeding(
            crime_id=form.crime_id.data,
            case_number=form.case_number.data,
            court_name=form.court_name.data,
            judge=form.judge.data,
            prosecutor=form.prosecutor.data,
            defense_attorney=form.defense_attorney.data,
            hearing_date=form.hearing_date.data,
            status=form.status.data,
            verdict=form.verdict.data,
            sentence=form.sentence.data,
            notes=form.notes.data
        )
        
        db.session.add(legal_proceeding)
        db.session.commit()
        
        log_activity(
            f"Legal proceeding created for crime ID: {legal_proceeding.crime_id}",
            f"Case Number: {legal_proceeding.case_number}, Status: {legal_proceeding.status}",
            current_user.id
        )
        
        flash('Legal proceeding has been created successfully.', 'success')
        
        # Redirect back to crime view if linked to a crime
        if crime_id:
            return redirect(url_for('crime_view', crime_id=crime_id))
        else:
            return redirect(url_for('legal_list'))
    
    return render_template('legal/create.html',
                          title='Create Legal Proceeding',
                          form=form,
                          crime_id=crime_id)

@app.route('/legal/view/<int:legal_id>')
@login_required
def legal_view(legal_id):
    """View legal proceeding details"""
    legal = LegalProceeding.query.get_or_404(legal_id)
    crime = Crime.query.get(legal.crime_id)
    
    # Check if user has permission to view this legal proceeding
    if not current_user.is_admin():
        if crime.reported_by != current_user.id:
            abort(403)
    
    return render_template('legal/view.html',
                          title=f'Legal Proceeding: {legal.case_number}',
                          legal=legal,
                          crime=crime)

@app.route('/legal/edit/<int:legal_id>', methods=['GET', 'POST'])
@login_required
def legal_edit(legal_id):
    """Edit legal proceeding"""
    legal = LegalProceeding.query.get_or_404(legal_id)
    crime = Crime.query.get(legal.crime_id)
    
    # Check if user has permission to edit this legal proceeding
    if not current_user.is_admin():
        if crime.reported_by != current_user.id:
            abort(403)
    
    form = LegalProceedingForm()
    
    # Populate crime dropdown
    if current_user.is_admin():
        form.crime_id.choices = [(c.id, c.title) for c in Crime.query.all()]
    else:
        form.crime_id.choices = [(c.id, c.title) for c in Crime.query.filter_by(reported_by=current_user.id).all()]
    
    if request.method == 'GET':
        form.crime_id.data = legal.crime_id
        form.case_number.data = legal.case_number
        form.court_name.data = legal.court_name
        form.judge.data = legal.judge
        form.prosecutor.data = legal.prosecutor
        form.defense_attorney.data = legal.defense_attorney
        form.hearing_date.data = legal.hearing_date
        form.status.data = legal.status
        form.verdict.data = legal.verdict
        form.sentence.data = legal.sentence
        form.notes.data = legal.notes
    
    if form.validate_on_submit():
        legal.crime_id = form.crime_id.data
        legal.case_number = form.case_number.data
        legal.court_name = form.court_name.data
        legal.judge = form.judge.data
        legal.prosecutor = form.prosecutor.data
        legal.defense_attorney = form.defense_attorney.data
        legal.hearing_date = form.hearing_date.data
        legal.status = form.status.data
        legal.verdict = form.verdict.data
        legal.sentence = form.sentence.data
        legal.notes = form.notes.data
        
        db.session.commit()
        
        log_activity(
            f"Legal proceeding updated for crime ID: {legal.crime_id}",
            f"Case Number: {legal.case_number}, Status: {legal.status}",
            current_user.id
        )
        
        flash('Legal proceeding has been updated successfully.', 'success')
        return redirect(url_for('legal_view', legal_id=legal.id))
    
    return render_template('legal/edit.html',
                          title='Edit Legal Proceeding',
                          form=form,
                          legal=legal)

@app.route('/legal/delete/<int:legal_id>', methods=['POST'])
@login_required
def legal_delete(legal_id):
    """Delete legal proceeding"""
    legal = LegalProceeding.query.get_or_404(legal_id)
    crime = Crime.query.get(legal.crime_id)
    
    # Check if user has permission to delete this legal proceeding
    if not current_user.is_admin():
        if crime.reported_by != current_user.id:
            abort(403)
    
    case_number = legal.case_number
    crime_id = legal.crime_id
    db.session.delete(legal)
    db.session.commit()
    
    log_activity(
        f"Legal proceeding deleted for crime ID: {crime_id}",
        f"Case Number: {case_number}",
        current_user.id
    )
    
    flash('Legal proceeding has been deleted.', 'success')
    return redirect(url_for('legal_list'))
