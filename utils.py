from functools import wraps
from flask import session, flash, redirect, url_for
from datetime import datetime

"""
Utility Helpers for W Notes+.
Contains shared decorators for security and formatting tools for data parsing.
"""

def login_required(f):
    """ensures a user session exists before allowing access."""
    # kicks unauthenticated users back to signin
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please sign in first.")
            return redirect(url_for('auth.signin'))
        return f(*args, **kwargs)
    return decorated_function

def parse_date(date_str):
    """
    Safely converts a date string into a Python object.
    due_date = None serves as an error handle for empty or invalid inputs.
    """
    # Returns None if the date is empty or invalid. 
    if date_str and date_str.strip():
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return None
    return None