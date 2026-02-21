from flask import Flask, render_template
from extensions import db
from model.models import lookup_data
from routes.auth import auth_bp
from routes.main import main_bp
from routes.tasks import tasks_bp

"""
Launches studyplanner webapp.
Initializes Flask, connects the database and plugs in the blueprints.
"""

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'readingthiskeys'

db.init_app(app)

app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)
app.register_blueprint(tasks_bp)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', code=404, message="404 page not found"), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        lookup_data() 
    app.run(host='0.0.0.0', port=5000, debug=True)