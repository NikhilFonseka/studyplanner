from app import app, db, User,resetdb

def run_test():
    resetdb()
    client = app.test_client()
    #erase database
    with app.app_context():
        #creates sample user
        response = client.post('/signup', data={
            'username': 'testuser',
            'email': 'test@gmail.com',
            'password': '123'
        }, follow_redirects=True)
        
        #query is similar to select * from user checks if the user is in the database if not it fails
        user = User.query.filter_by(username='testuser').first()
        if user:
            print("in database")
        else:
            print("fail")


        response = client.post('/signin', data={
            'username or email': 'test@gmail.com',
            'password': 'password123'
        }, follow_redirects=True)

        if b"Welcome" in response.data or b"Study Planner dashboard" in response.data:
            print("Pass (sign in successful)")
        else:
            print("Fail (sign in not successful)")


        fail_response = client.post('/signin', data={
            'username or email': 'test@school.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)

        if b"Invalid username or password" in fail_response.data:
            print("Pass (wrong password detected)")
        else:
            print("Fail (wrong password not detecteed)")
#good practice to include name = main for importing
if __name__ == '__main__':
    run_test()