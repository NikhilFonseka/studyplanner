from app import app, db, User,resetdb
import pytest
import sys
def run_test():
    resetdb()
    client = app.test_client()
    #erase database
    with app.app_context():
        #creates sample user
        response = client.post('/signup', data={
            'username': 'testuser',
            'email': 'test@gmail.com',
            'password': 'password123'
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

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_dashboard_loads(client):
    """Test if the dashboard returns a 200 OK status"""
    rv = client.get('/dashboard')
    assert rv.status_code == 200
    assert b"W Notes+" in rv.data

def test_navigation_links(client):
    """Test if the generated links are correct (not broken Jinja tags)"""
    rv = client.get('/dashboard')
    # This proves the {{ url_for }} worked and turned into a real path
    assert b'href="/logout"' in rv.data 
    assert b'href="/dashboard"' in rv.data

def test_empty_subjects_message(client):
    """Test the logic inside the <ul> (the 'else' case)"""
    rv = client.get('/dashboard')
    # If the database is empty, it should show your 'else' message
    assert b"You haven't added any subjects yet." in rv.data



#good practice to include name = main for importing
if __name__ == '__main__':
    run_test()
    #sys.exit(pytest.main([__file__]))
    