# pylint: disable=R0903
"""
W Notes+ is a flask based webapp
used as a all in one study tool that aims to maximise studying efficiency
"""

import os
import sys
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect, url_for, flash, session
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from werkzeug.security import generate_password_hash, check_password_hash
from jinja2 import Environment, FileSystemLoader, exceptions


def validate_templates():
    """Validates Jinja syntax to prevent errors during runtime."""
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    templates = [x for x in env.list_templates() if x.endswith('.html')]
    errors = 0
    for template in templates:
        try:
            env.get_template(template)
        except exceptions.TemplateSyntaxError:
            errors += 1
    if errors > 0:
        print(f"Validation failed with {errors} errors")
        sys.exit()


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'readingthiskeys'
db = SQLAlchemy(app)


# Models


class User(db.Model):
    """Table for application users."""

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)


class Subject(db.Model):
    """Table for subjects, linked to users."""

    subject_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    color_tag = db.Column(db.String(20))
    user_id = db.Column(
        db.Integer, db.ForeignKey('user.user_id'), nullable=False
    )
    tasks = db.relationship('Task', backref='subject', lazy=True)


class Task(db.Model):
    """Table for tasks, linked to subjects."""

    task_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    due_date = db.Column(db.DateTime)
    is_completed = db.Column(db.Boolean, default=False)
    subject_id = db.Column(
        db.Integer, db.ForeignKey('subject.subject_id'), nullable=False
    )


class Tag(db.Model):
    """Table for task tags for task categories or tags"""

    tag_id = db.Column(db.Integer, primary_key=True)
    tag_name = db.Column(db.String(20), nullable=False)


# Controllers


@app.route('/')
def index():
    """Redirects start URL to the sign-in page."""
    return redirect(url_for('signin'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handles new user registration"""
    if request.method == 'POST':
        user = request.form.get('username')
        email_address = request.form.get('email')
        password = request.form.get('password')
        hashed_password = generate_password_hash(password)
        new_user = User(
            username=user, email=email_address, password_hash=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('signin'))
    return render_template('signup.html')


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    """Authenticates users and manages session login"""
    if request.method == 'POST':
        login_identifier = request.form.get('username or email')
        pwd = request.form.get('password')
        record = User.query.filter(or_(
            User.username == login_identifier,
            User.email == login_identifier
        )).first()

        if record and check_password_hash(record.password_hash, pwd):
            session['user_id'] = record.user_id
            return redirect(url_for('dashboard'))

        flash("Invalid credentials")
        return render_template('signin.html'), 401
    return render_template('signin.html')


@app.route('/logout')
def logout():
    """Handles logging out (removing user from session)"""
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for('signin'))


@app.route('/dashboard')
def dashboard():
    """Handles the dashboard."""
    user_id = session.get('user_id')
    if user_id:
        user = db.session.get(User, user_id)
        user_subs = Subject.query.filter_by(user_id=user_id).all()
        return render_template(
            'home.html', username=user.username, subjects=user_subs
        )
    flash("Please login to access the dashboard.")
    return redirect(url_for('signin'))


@app.route('/add_subject', methods=['GET', 'POST'])
def add_subject():
    """Handles new subject creation."""
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    if request.method == 'POST':
        name = request.form.get('name')
        color = request.form.get('color')
        new_subject = Subject(
            name=name, color_tag=color, user_id=session['user_id']
        )
        db.session.add(new_subject)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('addsubject.html')


@app.route('/add_task', methods=['GET', 'POST'])
def add_task():
    """Adds a task to a specific subject with date validation"""
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    user_subjects = Subject.query.filter_by(user_id=session['user_id']).all()
    if request.method == 'POST':
        title = request.form.get('title')
        date_str = request.form.get('due_date')
        sub_id = request.form.get('subject_id')
        due_date = None
        if date_str and date_str.strip():
            try:
                due_date = datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                due_date = None
        new_task = Task(title=title, due_date=due_date, subject_id=sub_id)
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('addtask.html', subjects=user_subjects)


@app.route('/subject/<int:subject_id>')
def view_subject(subject_id):
    """Handles view of a subject and its tasks"""
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    subject = Subject.query.filter_by(
        subject_id=subject_id, user_id=session['user_id']
    ).first()
    if not subject:
        return "Unauthorized Access", 403
    return render_template('viewsubject.html', subject=subject)


@app.route('/complete_task/<int:task_id>')
def complete_task(task_id):
    """Task completion status."""
    task = Task.query.get_or_404(task_id)
    if task.subject.user_id == session.get('user_id'):
        task.is_completed = not task.is_completed
        db.session.commit()
    return redirect(request.referrer or url_for('dashboard'))


@app.route('/delete_subject/<int:subject_id>')
def delete_subject(subject_id):
    """Deletes a subject after verifying ownership"""
    subject = Subject.query.filter_by(
        subject_id=subject_id, user_id=session['user_id']
    ).first_or_404()
    db.session.delete(subject)
    db.session.commit()
    flash(f"Subject '{subject.name}' deleted")
    return redirect(url_for('dashboard'))


def resetdb():
    """Resets all database tables"""
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("database reset")


if __name__ == '__main__':
    validate_templates()
    with app.app_context():
        db.create_all()
    app.run(debug=True)
