from app import app, db, User

def run_test():
    client = app.test_client()
    #erase database
    with app.app_context():
        db.drop_all()
        db.create_all()

        response = client.post('/signup', data={
            'username': 'testuser',
            'email': 'test',
            'password': '123'
        }, follow_redirects=True)
        
        #query is similar to select * from user checks if the user is in the database if not it fails
        user = User.query.filter_by(username='testuser').first()
        if user:
            print("in database.")
        else:
            print("fail")

        response = client.post('/signin', data={
            'username or email': 'test',
            'password': '123'
        }, follow_redirects=True)
        #tries to sign in using the data from the created user earlier if it works pass else it fails
        if b"Login Complete" in response.data:
            print("pass")
        else:
            print("fail")
#good practice to include name = main for importing
if __name__ == '__main__':
    run_test()