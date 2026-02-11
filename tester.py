from app import app, db, User

def run_test():
    client = app.test_client()
    
    with app.app_context():
        db.drop_all()
        db.create_all()

        response = client.post('/signup', data={
            'username': 'testuser',
            'email': 'test',
            'password': '123'
        }, follow_redirects=True)
        

        user = User.query.filter_by(username='testuser').first()
        if user:
            print("in database.")
        else:
            print("fail")

        response = client.post('/signin', data={
            'username or email': 'test',
            'password': '123'
        }, follow_redirects=True)

        if b"Login Complete" in response.data:
            print("pass")
        else:
            print("fail")

run_test()