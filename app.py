from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_

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
#controller for sign up page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        user = request.form.get('username')
        emailaddress = request.form.get('email')
        pwd = request.form.get('password')
        
        hashed_pwd = generate_password_hash(pwd)
        
        new_user = User(username=user,email=emailaddress, password_hash=hashed_pwd)
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
        
        record = User.query.filter(or_(User.username==login_iden, User.email == login_iden)).first()
        

        if record and check_password_hash(record.password_hash, pwd):
            session['user_id'] = record.user_id
            return "Login Complete"
        else:
            return "Invalid username or password"
            
    return render_template('signin.html')
#bugged currently need to incorporate session
@app.route('/dashboard')
def dashboard():
    user = User.query.get('user_id')
    return render_template('home.html', username=user.username)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)