from extensions import db
from datetime import datetime, timezone, timedelta

"""
Database Schema for W Notes+. Models stored here
+ Look up structure
"""
# UCT+13 for NZDT 
def get_nzt_now():
    """Returns the current time in New Zealand (+13) for accurate logging."""
    nz_offset = timezone(timedelta(hours=13))
    return datetime.now(nz_offset)

# Many to Many helper for task tagging
task_tags = db.Table('task_tags',
    db.Column('task_id', db.Integer, db.ForeignKey('task.task_id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.tag_id'), primary_key=True)
)
# Lookup table for UI theme colors.
class Color(db.Model):
    """Lookup table for UI theme colors."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    hex_code = db.Column(db.String(7))
# Tracks task progress
class Status(db.Model):
    """Lookup table for task progress states."""
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(20)) 
# Tracks priority weight for tasks
class Priority(db.Model):
    """Lookup table for sorting tasks by importance."""

    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(20))
    weight = db.Column(db.Integer)
# Stores data for users
class User(db.Model):
    """Stores user credentials."""
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
# Stores data for subjects
class Subject(db.Model):
    """Stores info for subject."""
    subject_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    color_id = db.Column(db.Integer, db.ForeignKey('color.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    color = db.relationship('Color', backref='subjects')
    # If a subject is deleted all tasks are also deleted
    tasks = db.relationship('Task', backref='subject', lazy=True, cascade="all, delete-orphan")
    study_sessions = db.relationship('StudySession', backref='subject', lazy=True, cascade="all, delete-orphan")
    members = db.relationship('SubjectMember', backref='subject', lazy=True, cascade="all, delete-orphan")
# Stores data for tasks
class Task(db.Model):
    """Stores data for tasks."""
    task_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime)
    status_id = db.Column(db.Integer, db.ForeignKey('status.id'), default=1)
    priority_id = db.Column(db.Integer, db.ForeignKey('priority.id'))
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.subject_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    tags = db.relationship('Tag', secondary=task_tags, backref=db.backref('tasks', lazy='dynamic'))
#Logs study sessions
class StudySession(db.Model):
    """Logs actual study time."""
    id = db.Column(db.Integer, primary_key=True)
    duration = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.DateTime, default=get_nzt_now)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.subject_id'), nullable=False)
#Labels for organizing tasks
class Tag(db.Model):
    """Labels for organizing tasks."""
    tag_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
#Messaging system
class Message(db.Model):
    """Collaboration feed for the subject view."""
    message_id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=get_nzt_now)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.subject_id'), nullable=False)
    sender = db.relationship('User', backref='sent_messages')

    # Tracks if you have joined any subjects
class SubjectMember(db.Model):
    """Tracks who belongs to what subject and their invite status."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.subject_id'), nullable=False)
    status = db.Column(db.String(20), default='pending') 
    user = db.relationship('User', backref='subject_memberships')
#data for when DB is reset
def lookup_data():
    """When DB is reset this brings back default lookup data."""
    if not Tag.query.first():
        db.session.add_all([Tag(name='urgent'), Tag(name='exam'), Tag(name='general')])
    if not Priority.query.first():
        db.session.add_all([Priority(level='high', weight=1), Priority(level='normal', weight=2), Priority(level='low', weight=3)])
    if not Color.query.first():
        db.session.add_all([Color(name='blue', hex_code='#007BFF'), Color(name='orange', hex_code='#FF6B4A'), Color(name='green', hex_code='#28A745')])
    if not Status.query.first():
        db.session.add_all([Status(id=1, label='pending'), Status(id=2, label='completed')])
    db.session.commit()