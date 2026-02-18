# pylint: disable=redefined-outer-name
"""
Unit and Integration tests for W Notes+
Proves authentication, navigation, an integrity.
"""

import pytest
from app import app, db, Subject, StudySession, resetdb

@pytest.fixture
def client():
    """Pytest fixture to initialize the test client and database."""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        with app.app_context():
            resetdb()
            client.post('/signup', data={
                'username': 'testuser',
                'email': 'test@gmail.com',
                'password': 'password123'
            }, follow_redirects=True)
        yield client

def test_dashboard_access(client):
    """Proves the dashboard loads for a logged-in user."""
    client.post('/signin', data={
        'username or email': 'test@gmail.com',
        'password': 'password123'
    }, follow_redirects=True)
    rv = client.get('/dashboard')
    assert rv.status_code == 200
    assert b"W Notes+" in rv.data

def test_navigation_links(client):
    """Proves essential navigation links exist on the dashboard."""
    client.post('/signin', data={
        'username or email': 'test@gmail.com',
        'password': 'password123'
    }, follow_redirects=True)
    
    rv = client.get('/dashboard')
    assert b'href="/logout"' in rv.data.lower()
    assert b'href="/add_subject"' in rv.data.lower()

def test_add_subject(client):
    """Tests if a user can successfully create a subject and see it rendered."""
    client.post('/signin', data={
        'username or email': 'test@gmail.com',
        'password': 'password123'
    }, follow_redirects=True)

    rv = client.post('/add_subject', data={
        'name': 'Computing',
        'color': '#ff7543'
    }, follow_redirects=True)

    assert rv.status_code == 200
    assert b"computing" in rv.data.lower()

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

def test_study_session_logging(client):
    """Integration test studysession logging."""
    client.post('/signin', data={
        'username or email': 'test@gmail.com',
        'password': 'password123'
    }, follow_redirects=True)

    client.post('/add_subject', data={'name': 'Math', 'color': '#000000'})
    with app.app_context():
        subject = Subject.query.filter_by(name='Math').first()
        sub_id = subject.subject_id

    rv = client.post(f'/log_session/{sub_id}', data={
        'duration': '25'
    }, follow_redirects=True)

    assert b'25m' in rv.data.lower()

    with app.app_context():
        session_exists = StudySession.query.filter_by(subject_id=sub_id, duration=25).first()
        assert session_exists is not None

def test_messaging_system(client):
    """Proves messages can be sent and viewed within a subject."""
    client.post('/signin', data={'username or email': 'test@gmail.com', 'password': 'password123'}, follow_redirects=True)
    client.post('/add_subject', data={'name': 'Physics', 'color': '#000000'})
    
    with app.app_context():
        subject = Subject.query.filter_by(name='Physics').first()
        sub_id = subject.subject_id

    rv = client.post(f'/send_message/{sub_id}', data={
        'content': 'Check the lab notes'
    }, follow_redirects=True)

    assert b'check the lab notes' in rv.data.lower()

if __name__ == '__main__':
    pytest.main([__file__])
    resetdb()