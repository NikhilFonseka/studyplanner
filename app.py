# pylint: disable=R0903
"""
W Notes+ | Sprint 3
Used as a all in one study tool that aims to maximise studying efficiency.
"""
from functools import wraps
from datetime import datetime, timezone, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'readingthiskeys'
db = SQLAlchemy(app)


def get_nzt_now():
    # UCT+13 for New Zealand Daylight Time
    nz_offset = timezone(timedelta(hours=13))
    return datetime.now(nz_offset)

def login_required(f):
    # Standard wrapper to kick unauthenticated users back to signin
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please sign in first.")
            return redirect(url_for('signin'))
        return f(*args, **kwargs)
    return decorated_function

def parse_date(date_str):
    # Returns None if the user leaves the date empty or types something weird
    # This acts as the primary error handle for task deadlines
    if date_str and date_str.strip():
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return None
    return None

# Database Models (3NF) 

class Color(db.Model):
    # Stores hex codes don't hardcode styles in the DB
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    hex_code = db.Column(db.String(7))

class Status(db.Model):
    # Status for tasks
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(20)) 

class Priority(db.Model):
    # Weights help us sort tasks by importance later
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(20))
    weight = db.Column(db.Integer)

# Helper table for the many-to-many relationship between tasks and tags
task_tags = db.Table('task_tags',
    db.Column('task_id', db.Integer, db.ForeignKey('task.task_id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.tag_id'), primary_key=True)
)

class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

class Subject(db.Model):
    subject_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    color_id = db.Column(db.Integer, db.ForeignKey('color.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    color = db.relationship('Color', backref='subjects')
    # Cleanup tasks/sessions if a subject is deleted
    tasks = db.relationship('Task', backref='subject', lazy=True, cascade="all, delete-orphan")
    study_sessions = db.relationship('StudySession', backref='subject', lazy=True, cascade="all, delete-orphan")
    members = db.relationship('SubjectMember', backref='subject', lazy=True, cascade="all, delete-orphan")

class Task(db.Model):
    task_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime)
    status_id = db.Column(db.Integer, db.ForeignKey('status.id'), default=1)
    priority_id = db.Column(db.Integer, db.ForeignKey('priority.id'))
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.subject_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    tags = db.relationship('Tag', secondary=task_tags, backref=db.backref('tasks', lazy='dynamic'))

class StudySession(db.Model):
    # Track how long we actually studied for a specific subject
    id = db.Column(db.Integer, primary_key=True)
    duration = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.DateTime, default=get_nzt_now)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.subject_id'), nullable=False)

class Tag(db.Model):
    tag_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)

class Message(db.Model):
    # For the collaboration feed
    message_id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=get_nzt_now)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.subject_id'), nullable=False)
    sender = db.relationship('User', backref='sent_messages')

class SubjectMember(db.Model):
    # Tracks who is invited to which subject and if they've accepted
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.subject_id'), nullable=False)
    status = db.Column(db.String(20), default='pending') 
    user = db.relationship('User', backref='subject_memberships')

# Routes 
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', 
        code=404, 
        message="404 page not found", 
        description="The page you're looking for doesn't exist or has been moved."), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', 
        code=500, 
        message="internal glitch", 
        description="Something went wrong on our end. We're looking into it."), 500

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('signin'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        user = request.form.get('username')
        email_address = request.form.get('email')
        password = request.form.get('password')


        existing_user = User.query.filter(
            (User.username == user) | (User.email == email_address)).first()
        if existing_user:
            flash("Username or email already in use. Login instead?")
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password)
        new_user = User(username=user, email=email_address, password_hash=hashed_password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('signin'))
        except Exception:
            db.session.rollback()
            flash("An error occurred during registration. Please try again.")
            return redirect(url_for('signup'))

    return render_template('signup.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        login_identifier = request.form.get('username or email')
        pwd = request.form.get('password')
        record = User.query.filter(or_(User.username == login_identifier, User.email == login_identifier)).first()
        if record and check_password_hash(record.password_hash, pwd):
            session['user_id'] = record.user_id
            return redirect(url_for('dashboard'))
        flash("Invalid credentials")
        return render_template('signin.html'), 401
    return render_template('signin.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for('signin'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    user = db.session.get(User, user_id)
    owned_subs = Subject.query.filter_by(user_id=user_id).all()
    
    others_memberships = SubjectMember.query.filter(
        SubjectMember.user_id == user_id, 
        SubjectMember.status == 'accepted'
    ).all()
    shared_subs = [m.subject for m in others_memberships if m.subject.user_id != user_id]
    
    all_subjects = owned_subs + shared_subs
    pending_invites = SubjectMember.query.filter_by(user_id=user_id, status='pending').all()

    subject_list = []
    for s in all_subjects:
        active_count = Task.query.filter_by(subject_id=s.subject_id).filter(Task.status_id != 2).count()
        subject_list.append({
            'obj': s,
            'active_count': active_count
        })
    
    return render_template('home.html', 
                           username=user.username, 
                           subjects=subject_list, 
                           invites=pending_invites)

@app.route('/add_subject', methods=['GET', 'POST'])
@login_required
def add_subject():
    # Need these for the color picker dropdown
    available_colors = Color.query.all()
    if request.method == 'POST':
        name = request.form.get('name').strip()
        color_id = request.form.get('color_id')
        user_id = session['user_id']
        
        # Prevent duplicate subject names for the same user
        existing = Subject.query.filter(Subject.user_id == user_id, db.func.lower(Subject.name) == db.func.lower(name)).first()
        if existing:
            flash(f"Subject '{name}' already exists!")
            return redirect(url_for('dashboard'))
            
        new_subject = Subject(name=name, color_id=color_id, user_id=user_id)
        db.session.add(new_subject)
        db.session.flush() # Flush to get the ID for the membership record
        
        # Creator is automatically an accepted member
        owner_member = SubjectMember(user_id=user_id, subject_id=new_subject.subject_id, status='accepted')
        db.session.add(owner_member)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('addsubject.html', colors=available_colors)

@app.route('/add_task', methods=['GET', 'POST'])
@login_required
def add_task():
    user_id = session['user_id']
    # Only let users add tasks to subjects they actually belong to
    memberships = SubjectMember.query.filter_by(user_id=user_id, status='accepted').all()
    user_subjects = [m.subject for m in memberships]

    available_tags = Tag.query.all()
    available_priorities = Priority.query.order_by(Priority.weight.asc()).all()
    if request.method == 'POST':
        due_date = parse_date(request.form.get('due_date_str'))
        new_task = Task(
            title=request.form.get('title'),
            description=request.form.get('description'),
            due_date=due_date,
            subject_id=request.form.get('subject_id'),
            user_id=user_id,
            priority_id=request.form.get('priority_id')
            
        )
        # Link multiple tags from the checkbox list
        for t_id in request.form.getlist('tag_ids'):
            tag_obj = db.session.get(Tag, t_id)
            if tag_obj: new_task.tags.append(tag_obj)
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('view_subject', subject_id=new_task.subject_id))
    return render_template('addtask.html', subjects=user_subjects,
                           tags=available_tags,
                           priorities=available_priorities)

@app.route('/subject/<int:subject_id>')
@login_required
def view_subject(subject_id):
    user_id = session['user_id']
    subject = db.session.get(Subject, subject_id) or abort(404)
    membership = SubjectMember.query.filter_by(user_id=user_id, subject_id=subject_id, status='accepted').first()
    
    # Check if user has permission to see this subject
    if subject.user_id != user_id and not membership:
        flash("Access denied.")
        return redirect(url_for('dashboard'))
    
    sorted_tasks = Task.query.join(Priority).filter(Task.subject_id == subject_id).order_by(Task.status_id.asc(), Priority.weight.asc()).all()
        
    messages = Message.query.filter_by(subject_id=subject_id).order_by(Message.timestamp.asc()).all()
    return render_template('viewsubject.html', subject=subject,tasks=sorted_tasks, messages=messages)

@app.route('/log_session/<int:subject_id>', methods=['POST'])
@login_required
def log_session(subject_id):
    # Simple validation for study time
    duration_raw = request.form.get('duration')
    if not duration_raw or not duration_raw.isdigit() or int(duration_raw) <= 0:
        flash("Can't log 0 minutes.")
    else:
        new_session = StudySession(duration=int(duration_raw), subject_id=subject_id)
        db.session.add(new_session)
        db.session.commit()
    return redirect(url_for('view_subject', subject_id=subject_id))

@app.route('/send_message/<int:subject_id>', methods=['POST'])
@login_required
def send_message(subject_id):
    content = request.form.get('content')
    if content and content.strip():
        new_msg = Message(content=content, sender_id=session['user_id'], subject_id=subject_id)
        db.session.add(new_msg)
        db.session.commit()
    return redirect(url_for('view_subject', subject_id=subject_id))

@app.route('/invite_user/<int:subject_id>', methods=['POST'])
@login_required
def invite_user(subject_id):
    username = request.form.get('username')
    target_user = User.query.filter_by(username=username).first()
    if target_user:
        # Don't invite someone who is already there
        exists = SubjectMember.query.filter_by(user_id=target_user.user_id, subject_id=subject_id).first()
        if not exists:
            db.session.add(SubjectMember(user_id=target_user.user_id, subject_id=subject_id))
            db.session.commit()
            flash(f"Invite sent to {username}!")
        else: flash("User already a member or invited.") 
    else: flash(f"User '{username}' not found.")
    return redirect(url_for('view_subject', subject_id=subject_id))

@app.route('/accept_invite/<int:membership_id>')
@login_required
def accept_invite(membership_id):
    member = db.session.get(SubjectMember, membership_id) or abort(404)
    # Security check
    if member.user_id == session['user_id']:
        member.status = 'accepted'
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/delete_subject/<int:subject_id>')
@login_required
def delete_subject(subject_id):
    # Only the owner can delete the whole subject
    subject = Subject.query.filter_by(subject_id=subject_id, user_id=session['user_id']).first_or_404()
    db.session.delete(subject)
    db.session.commit()
    flash(f"Subject '{subject.name}' deleted.")
    return redirect(url_for('dashboard'))
@app.route('/complete_task/<int:task_id>')
@login_required
def complete_task(task_id):
    task = db.session.get(Task, task_id) or abort(404)

    if task.user_id != session['user_id']:
        flash("Permission denied.")
        return redirect(url_for('dashboard'))

    task.status_id = 2
    db.session.commit()
    
    return redirect(url_for('view_subject', subject_id=task.subject_id))
# DB setup

def lookup_data():
    # adds options if the DB is empty eg fresh reset
    if not Tag.query.first():
        db.session.add_all([Tag(name='urgent'), Tag(name='exam'), Tag(name='general')])
    if not Priority.query.first():
        db.session.add_all([Priority(level='high', weight=1), Priority(level='normal', weight=2), Priority(level='low', weight=3)])
    if not Color.query.first():
        db.session.add_all([Color(name='blue', hex_code='#007BFF'), Color(name='orange', hex_code='#FF6B4A'), Color(name='green', hex_code='#28A745')])
    if not Status.query.first():
        db.session.add_all([
            Status(id=1, label='pending'),
            Status(id=2, label='completed')
        ])
    db.session.commit()
    

def resetdb():
    """Wipes the database and recreates the structure. 
    Note: Lookup tables will be empty after this.
    """
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("worked")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        lookup_data()
    # Debug mode on for local dev
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)