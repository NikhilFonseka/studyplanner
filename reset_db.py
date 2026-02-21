from run import app
from extensions import db

def resetdb():
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Database reset and seeded successfully.")

if __name__ == "__main__":
    resetdb()