# pylint: disable=redefined-outer-name
"""
Unit and Integration tests for the W Notes+
used prove authentication and web display elements
"""

import pytest
from app import app, db, User, resetdb, Subject


def run_test():
    """Manual test runner for signing in into the site."""
    resetdb()
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
            print("User not in database.")
            return

        response = client.post('/signin', data={
            'username or email': 'test@gmail.com',
            'password': 'password123'
        }, follow_redirects=True)

        dashboard_check = (b"testuser" in response.data or
                           b"Dashboard" in response.data or
                           b"W Notes+" in response.data)

        if dashboard_check:
            print("Pass (signin successful and redirected to Dashboard)")
        else:
            print("Fail (Login failed or didn't reach dashboard)")
            print(f"response code {response.status_code}")


@pytest.fixture
def client():
    """Pytest fixture to initialize the test client and database."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        with app.app_context():
            resetdb()
            # register the user once for the pytest session
            client.post('/signup', data={
                'username': 'testuser',
                'email': 'test@gmail.com',
                'password': 'password123'
            }, follow_redirects=True)
        yield client


def test_dashboard_access(client):
    """Proves the dashboard loads for a logged in user."""
    client.post('/signin', data={
        'username or email': 'test@gmail.com',
        'password': 'password123'
    }, follow_redirects=True)
    rv = client.get('/dashboard')
    assert rv.status_code == 200
    assert b"W Notes+" in rv.data


def test_navigation_links(client):
    """Proves all navigation links are functional."""
    client.post('/signin', data={
        'username or email': 'test@gmail.com',
        'password': 'password123'
    }, follow_redirects=True)
    rv = client.get('/dashboard')
    assert b'href="/logout"' in rv.data
    assert b'href="/add_subject"' in rv.data
    assert b'href="/add_task"' in rv.data


def test_add_subject(client):
    """Tests if a user can successfully create a subject."""
    client.post('/signin', data={
        'username or email': 'test@gmail.com',
        'password': 'password123'
    }, follow_redirects=True)

    rv = client.post('/add_subject', data={
        'name': 'Computing',
        'color': '#ff7543'
    }, follow_redirects=True)

    assert rv.status_code == 200
    assert b"Computing" in rv.data


def test_unauthorized_subject_access(client):
    """Proves a user cannot see another user's subject (403 check)."""
    with app.app_context():
        enemy_sub = Subject(name="secret subject", user_id=99)
        db.session.add(enemy_sub)
        db.session.commit()
        enemy_id = enemy_sub.subject_id

    client.post('/signin', data={
        'username or email': 'test@gmail.com',
        'password': 'password123'
    }, follow_redirects=True)
    rv = client.get(f'/subject/{enemy_id}')

    assert rv.status_code == 403


if __name__ == '__main__':
    run_test()
    pytest.main([__file__])
