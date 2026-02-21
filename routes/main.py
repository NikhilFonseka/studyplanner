from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from extensions import db
from model.models import User, Subject, SubjectMember, Task, Message, Color, Priority, StudySession
from utils import login_required

"""
Main Application Blueprint.
Manages the dashboard, subject creation, collaboration invites, and messaging.
"""

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """
    The main entrance to W Notes+. 
    Checks if you're already logged in so you don't have to keep signing in.
    """
    if 'user_id' in session:
        # If we know who you are, head to the dashboard
        return redirect(url_for('main.dashboard'))
    
    # Otherwise, back to the login screen
    return redirect(url_for('auth.signin'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Renders the main study hub showing owned and joined subjects."""
    user_id = session['user_id']
    user = db.session.get(User, user_id)
    
    # Grab subjects the user owns and subjects they've been invited to
    owned_subs = Subject.query.filter_by(user_id=user_id).all()
    others_memberships = SubjectMember.query.filter(SubjectMember.user_id == user_id, SubjectMember.status == 'accepted').all()
    shared_subs = [m.subject for m in others_memberships if m.subject.user_id != user_id]
    
    all_subjects = owned_subs + shared_subs
    pending_invites = SubjectMember.query.filter_by(user_id=user_id, status='pending').all()

    # For sending to home
    subject_list = []
    for s in all_subjects:
        active_count = Task.query.filter_by(subject_id=s.subject_id).filter(Task.status_id != 2).count()
        subject_list.append({'obj': s, 'active_count': active_count})
    
    return render_template('home.html', username=user.username, subjects=subject_list, invites=pending_invites)

@main_bp.route('/add_subject', methods=['GET', 'POST'])
@login_required
def add_subject():
    """Creates a new subject and automatically joins the creator as a member."""
    available_colors = Color.query.all()
    if request.method == 'POST':
        name = request.form.get('name').strip()
        color_id = request.form.get('color_id')
        user_id = session['user_id']
        
        # Cant let them make the same subject twice
        existing = Subject.query.filter(Subject.user_id == user_id, db.func.lower(Subject.name) == db.func.lower(name)).first()
        if existing:
            flash(f"Subject '{name}' already exists!")
            return redirect(url_for('main.dashboard'))
            
        new_subject = Subject(name=name, color_id=color_id, user_id=user_id)
        db.session.add(new_subject)
        db.session.flush() 
        
        # Make the owner an member automatically
        owner_member = SubjectMember(user_id=user_id, subject_id=new_subject.subject_id, status='accepted')
        db.session.add(owner_member)
        db.session.commit()
        return redirect(url_for('main.dashboard'))
    return render_template('addsubject.html', colors=available_colors)

@main_bp.route('/subject/<int:subject_id>')
@login_required
def view_subject(subject_id):
    """Displays the specific workspace for a subject, including tasks and chat."""
    user_id = session['user_id']
    subject = db.session.get(Subject, subject_id) or abort(404)
    membership = SubjectMember.query.filter_by(user_id=user_id, subject_id=subject_id, status='accepted').first()
    
    # Simple permission check
    if subject.user_id != user_id and not membership:
        flash("Access denied.")
        return redirect(url_for('main.dashboard'))
    
    # Sort tasks by status and priority weight
    sorted_tasks = Task.query.join(Priority).filter(Task.subject_id == subject_id).order_by(Task.status_id.asc(), Priority.weight.asc()).all()
    messages = Message.query.filter_by(subject_id=subject_id).order_by(Message.timestamp.asc()).all()
    
    return render_template('viewsubject.html', subject=subject, tasks=sorted_tasks, messages=messages)
@main_bp.route('/log_session/<int:subject_id>', methods=['POST'])
@login_required
def log_session(subject_id):
    duration_raw = request.form.get('duration')
    if not duration_raw or not duration_raw.isdigit() or int(duration_raw) <= 0:
        flash("Can't log 0 minutes.")
    else:
        # Note: Ensure StudySession is imported from model.models
        new_session = StudySession(duration=int(duration_raw), subject_id=subject_id)
        db.session.add(new_session)
        db.session.commit()
    return redirect(url_for('main.view_subject', subject_id=subject_id))

@main_bp.route('/send_message/<int:subject_id>', methods=['POST'])
@login_required
def send_message(subject_id):
    content = request.form.get('content')
    if content and content.strip():
        new_msg = Message(content=content, sender_id=session['user_id'], subject_id=subject_id)
        db.session.add(new_msg)
        db.session.commit()
    return redirect(url_for('main.view_subject', subject_id=subject_id))

@main_bp.route('/invite_user/<int:subject_id>', methods=['POST'])
@login_required
def invite_user(subject_id):
    username = request.form.get('username')
    target_user = User.query.filter_by(username=username).first()
    if target_user:
        exists = SubjectMember.query.filter_by(user_id=target_user.user_id, subject_id=subject_id).first()
        if not exists:
            db.session.add(SubjectMember(user_id=target_user.user_id, subject_id=subject_id))
            db.session.commit()
            flash(f"Invite sent to {username}!")
        else:
            flash("User already a member or invited.") 
    else:
        flash(f"User '{username}' not found.")
    return redirect(url_for('main.view_subject', subject_id=subject_id))

@main_bp.route('/accept_invite/<int:membership_id>')
@login_required
def accept_invite(membership_id):
    member = db.session.get(SubjectMember, membership_id) or abort(404)
    if member.user_id == session['user_id']:
        member.status = 'accepted'
        db.session.commit()
    return redirect(url_for('main.dashboard'))

@main_bp.route('/delete_subject/<int:subject_id>')
@login_required
def delete_subject(subject_id):
    # Security check: Only the owner (creator) can delete
    subject = Subject.query.filter_by(subject_id=subject_id, user_id=session['user_id']).first_or_404()
    db.session.delete(subject)
    db.session.commit()
    flash(f"Subject '{subject.name}' deleted.")
    return redirect(url_for('main.dashboard'))