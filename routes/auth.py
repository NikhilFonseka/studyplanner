from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_
from extensions import db
from model.models import User

"""
Authentication Blueprint.
Handles registration, login, and secure logout logic using hashed passwords.
"""

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """Creates a new user account if the username/email is unique."""
    if request.method == 'POST':
        user = request.form.get('username')
        email_address = request.form.get('email')
        password = request.form.get('password')

        # Check if they're already in the system
        existing_user = User.query.filter((User.username == user) | (User.email == email_address)).first()
        if existing_user:
            flash("Username or email already in use. Login instead?")
            return redirect(url_for('auth.signup'))

        hashed_password = generate_password_hash(password)
        new_user = User(username=user, email=email_address, password_hash=hashed_password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('auth.signin'))
        except Exception:
            db.session.rollback()
            flash("An error occurred during registration. Please try again.")
            return redirect(url_for('auth.signup'))
    return render_template('signup.html')

@auth_bp.route('/signin', methods=['GET', 'POST'])
def signin():
    """Validates user credentials and initiates a session."""
    if request.method == 'POST':
        login_identifier = request.form.get('username or email')
        pwd = request.form.get('password')
        record = User.query.filter(or_(User.username == login_identifier, User.email == login_identifier)).first()
        
        if record and check_password_hash(record.password_hash, pwd):
            session['user_id'] = record.user_id
            return redirect(url_for('main.dashboard'))
        
        flash("Invalid credentials")
        return render_template('signin.html'), 401
    return render_template('signin.html')

@auth_bp.route('/logout')
def logout():
    """Clears the session and sends the user to signin page."""
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for('auth.signin'))