from app import app, db, User, resetdb
import pytest


def run_test():
    resetdb()
#tests signing in into the site
    client = app.test_client()
    
    with app.app_context():
        # create the user
        client.post('/signup', data={
            'username': 'testuser',
            'email': 'test@gmail.com',
            'password': 'password123'
        }, follow_redirects=True)
        
        # verify database insertion
        user = User.query.filter_by(username='testuser').first()
        if user:
            print("User created in database.")
        else:
            print("User not database.")
            return

        response = client.post('/signin', data={
            'username or email': 'test@gmail.com',
            'password': 'password123'
        }, follow_redirects=True)


        if b"testuser" in response.data or b"Dashboard" in response.data or b"W Notes+" in response.data:
            print("Pass (signin successful and redirected to Dashboard)")
        else:
            print("Fail (Login failed or didn't reach dashboard)")
            #log a of the response to see what happened
            print(f"response code {response.status_code}")

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  
    with app.test_client() as client:
        with app.app_context():
            resetdb()
            # register the user once for the pytest session
            client.post('/signup', data={
                'username': 'testuser', 'email': 'test@gmail.com', 'password': 'password123'
            }, follow_redirects=True)
        yield client

def test_dashboard_access(client):
    #Proves the dashboard loads for a logged in user
    client.post('/signin', data={'username or email': 'test@gmail.com', 'password': 'password123'}, follow_redirects=True)
    rv = client.get('/dashboard')
    assert rv.status_code == 200
    assert b"W Notes+" in rv.data

def test_navigation_links(client):
    #proves all links are functional
    client.post('/signin', data={'username or email': 'test@gmail.com', 'password': 'password123'}, follow_redirects=True)
    rv = client.get('/dashboard')
    assert b'href="/logout"' in rv.data
    # Look for these instead:
    assert b'href="/add_subject"' in rv.data
    assert b'href="/add_task"' in rv.data

def test_empty_subjects_message(client):
    client.post('/signin', data={'username or email': 'test@gmail.com', 'password': 'password123'}, follow_redirects=True)
    rv = client.get('/dashboard')
    assert b'No subjects yet. Click "Add New Subject" to start!' in rv.data



if __name__ == '__main__':
    run_test()
    pytest.main([__file__])