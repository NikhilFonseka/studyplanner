from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = "W_notes+"
db = SQLAlchemy(app)
#user table
class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

#subjects table
class Subject(db.Model):
    subject_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    color_tag = db.Column(db.String(20)) 
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    tasks = db.relationship('Task', backref='subject', lazy=True)
#tasks table
class Task(db.Model):
    task_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    due_date = db.Column(db.DateTime, nullable=True)
    is_completed = db.Column(db.Boolean, default=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.subject_id'), nullable=False)

@app.route('/')
def index():
    # auto redirects to signin page when the default site http://127.0.0.1:5000 is visited
    return redirect(url_for('signin'))
#controller for sign up page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        user = request.form.get('username')
        emailaddress = request.form.get('email')
        pwd = request.form.get('password')
        hashed_pwd = generate_password_hash(pwd)
        new_user = User(username=user, email=emailaddress, password_hash=hashed_pwd)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('signin'))
    return render_template('signup.html')
#controller for sign in page
@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        login_iden = request.form.get('username or email')
        pwd = request.form.get('password')
        
        record = User.query.filter(or_(User.username == login_iden, User.email == login_iden)).first()

        if record and check_password_hash(record.password_hash, pwd):
            session['user_id'] = record.user_id

            return redirect(url_for('dashboard')) 
        else:
            flash("Invalid username or password")
            return render_template('signin.html')
            
    return render_template('signin.html')
#controller for logout
@app.route('/logout')
def logout():
    session.clear() 
    flash("You have been logged out.") 
    return redirect(url_for('signin'))

#controller for dashboard
@app.route('/dashboard')
def dashboard():
    #checks if user id is the sessions pool, if not kick the userout to prevent unauthroized access
    user_id = session.get('user_id')
    if user_id:
        user = db.session.get(User, user_id) 
        user_subs = Subject.query.filter_by(user_id=user_id).all()
        return render_template('home.html', username=user.username, subjects=user_subs)
    flash("Please login to access the dashboard.")
    return redirect(url_for('signin'))

#add subject controller
@app.route('/add_subject', methods=['GET', 'POST'])
def add_subject():
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        color = request.form.get('color')
        new_sub = Subject(name=name, color_tag=color, user_id=session['user_id'])
        db.session.add(new_sub)
        db.session.commit()
        return redirect(url_for('dashboard'))
    
    return render_template('addsubject.html')
#add task controller
@app.route('/add_task', methods=['GET', 'POST'])
def add_task():
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    
    user_subjects = Subject.query.filter_by(user_id=session['user_id']).all()

    if request.method == 'POST':
        title = request.form.get('title')
        due_date_str = request.form.get('due_date')
        sub_id = request.form.get('subject_id')
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d') if due_date_str else None
        
        new_task = Task(title=title, due_date=due_date, subject_id=sub_id)
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('addtask.html', subjects=user_subjects)

#viewsubject controller
@app.route('/subject/<int:subject_id>')
def view_subject(subject_id):
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    #data secruity
    subject = Subject.query.filter_by(subject_id=subject_id, user_id=session['user_id']).first_or_404()
    return render_template('viewsubject.html', subject=subject)

#completed task controller
@app.route('/complete_task/<int:task_id>')
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)
    if task.subject.user_id == session.get('user_id'):
        task.is_completed = not task.is_completed  # mark as complete or not
        db.session.commit()
    return redirect(request.referrer or url_for('dashboard'))

#subject delete controller
@app.route('/delete_subject/<int:subject_id>')
def delete_subject(subject_id):
    subject = Subject.query.filter_by(subject_id=subject_id, user_id=session['user_id']).first_or_404()
    db.session.delete(subject)
    db.session.commit()
    flash(f"Subject '{subject.name}' deleted.")
    return redirect(url_for('dashboard'))

#for when I need to reset db for testing purposes will not be used in the finished product but useful feature
def resetdb():
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("database reset")
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)