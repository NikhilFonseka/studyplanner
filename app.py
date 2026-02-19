# pylint: disable=R0903
"""
W Notes+ | Sprint 3 Refactored
Clean 3NF architecture with optimized decorators and NZDT support.
"""
from functools import wraps
from datetime import datetime, timezone, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'readingthiskeys'
db = SQLAlchemy(app)


def get_nzt_now():
    """Returns current time with a fixed UTC+13 offset (NZDT)."""
    return datetime.now(timezone(timedelta(hours=13)))

def login_required(f):
    """Decorator to protect routes from unauthorized access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please sign in first.")
            return redirect(url_for('signin'))
        return f(*args, **kwargs)
    return decorated_function

def parse_date(date_str):
    """Handles the due_date error logic requested for Sprint 3."""
    if date_str and date_str.strip():
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return None
    return None


class Color(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    hex_code = db.Column(db.String(7))

class Status(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(20)) 

class Priority(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(20))
    weight = db.Column(db.Integer)

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
    tasks = db.relationship('Task', backref='subject', cascade="all, delete-orphan")
    study_sessions = db.relationship('StudySession', backref='subject', cascade="all, delete-orphan")

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
    id = db.Column(db.Integer, primary_key=True)
    duration = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.DateTime, default=get_nzt_now)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.subject_id'), nullable=False)

class Tag(db.Model):
    tag_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)

class Message(db.Model):
    message_id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=get_nzt_now)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.subject_id'), nullable=False)
    sender = db.relationship('User', backref='sent_messages')

class SubjectMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.subject_id'), nullable=False)
    status = db.Column(db.String(20), default='pending') 
    user = db.relationship('User', backref='subject_memberships')
    subject = db.relationship('Subject', backref='members')


@app.route('/')
def index():
    return redirect(url_for('signin'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        new_user = User(
            username=request.form.get('username'),
            email=request.form.get('email'),
            password_hash=generate_password_hash(request.form.get('password'))
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('signin'))
    return render_template('signup.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        login_id = request.form.get('username or email')
        pwd = request.form.get('password')
        user = User.query.filter(or_(User.username == login_id, User.email == login_id)).first()
        if user and check_password_hash(user.password_hash, pwd):
            session['user_id'] = user.user_id
            return redirect(url_for('dashboard'))
        flash("Invalid credentials")
    return render_template('signin.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for('signin'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = db.session.get(User, session['user_id'])
    # Using 3NF Relationships to get subjects
    owned_subs = Subject.query.filter_by(user_id=user.user_id).all()
    shared_subs = [m.subject for m in user.subject_memberships if m.status == 'accepted' and m.subject.user_id != user.user_id]
    invites = [m for m in user.subject_memberships if m.status == 'pending']
    return render_template('home.html', username=user.username, subjects=owned_subs + shared_subs, invites=invites)

@app.route('/add_subject', methods=['GET', 'POST'])
@login_required
def add_subject():
    if request.method == 'POST':
        name = request.form.get('name').strip()
        new_sub = Subject(name=name, color_id=request.form.get('color_id'), user_id=session['user_id'])
        db.session.add(new_sub)
        db.session.flush()
        # Automatically make owner an accepted member
        db.session.add(SubjectMember(user_id=session['user_id'], subject_id=new_sub.subject_id, status='accepted'))
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('addsubject.html', colors=Color.query.all())

@app.route('/add_task', methods=['GET', 'POST'])
@login_required
def add_task():
    user = db.session.get(User, session['user_id'])
    if request.method == 'POST':
        sub_id = request.form.get('subject_id')
        new_task = Task(
            title=request.form.get('title'),
            description=request.form.get('description'),
            due_date=parse_date(request.form.get('due_date_str')),
            subject_id=sub_id,
            user_id=user.user_id
        )
        for t_id in request.form.getlist('tag_ids'):
            tag_obj = db.session.get(Tag, t_id)
            if tag_obj: new_task.tags.append(tag_obj)
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('view_subject', subject_id=sub_id))
    
    user_subjects = [m.subject for m in user.subject_memberships if m.status == 'accepted']
    return render_template('addtask.html', subjects=user_subjects, tags=Tag.query.all())

@app.route('/subject/<int:subject_id>')
@login_required
def view_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    is_member = SubjectMember.query.filter_by(user_id=session['user_id'], subject_id=subject_id, status='accepted').first()
    if not is_member:
        flash("Access denied.")
        return redirect(url_for('dashboard'))
    
    messages = Message.query.filter_by(subject_id=subject_id).order_by(Message.timestamp.asc()).all()
    return render_template('viewsubject.html', subject=subject, messages=messages)

@app.route('/send_message/<int:subject_id>', methods=['POST'])
@login_required
def send_message(subject_id):
    content = request.form.get('content')
    if content and content.strip():
        db.session.add(Message(content=content, sender_id=session['user_id'], subject_id=subject_id))
        db.session.commit()
    return redirect(url_for('view_subject', subject_id=subject_id))



def lookup_data():
    """Seeds lookup tables if they are empty."""
    if not Tag.query.first():
        db.session.add_all([Tag(name='urgent'), Tag(name='exam'), Tag(name='general')])
    if not Priority.query.first():
        db.session.add_all([Priority(level='urgent', weight=1), Priority(level='normal', weight=2), Priority(level='low', weight=3)])
    if not Color.query.first():
        db.session.add_all([Color(name='blue', hex_code='#007BFF'), Color(name='orange', hex_code='#FF6B4A'), Color(name='green', hex_code='#28A745')])
    db.session.commit()
    print("All lookup data seeded successfully.")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        lookup_data()
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)