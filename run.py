from flask import Flask, render_template
from extensions import db
from model.models import lookup_data
from routes.auth import auth_bp
from routes.main import main_bp
from routes.tasks import tasks_bp

"""
Main Application Entry Point.
Initializes the Flask app, connects the database, and registers all blueprints.
"""

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'readingthiskeys'

# Connect the DB object to this specific app instance
db.init_app(app)

# route blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)
app.register_blueprint(tasks_bp)

# Error handlers visiblity of system status
@app.errorhandler(404)
def page_not_found(e):
    """404 error page. Visiblity of system status."""
    return render_template('error.html', code=404, message="404 page not found"), 404

@app.errorhandler(500)
def server_error(e):
    """505 error page visiblity of system status."""
    return render_template('error.html', code=500, message="internal glitch", description="Something went wrong on our end. We're looking into it."), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        lookup_data() # Seed the basics if the DB is empty
    # Port 5000 is the standard dev spot
    app.run(host='0.0.0.0', port=5000, debug=True)