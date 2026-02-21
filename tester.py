import pytest
from run import app
from extensions import db
from model.models import Subject, Task, SubjectMember, Priority, lookup_data
from reset_db import resetdb

@pytest.fixture
def client():
    """Setup a fresh database for every test run."""
    app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SERVER_NAME': 'localhost'
    })
    
    with app.test_client() as client:
        with app.app_context():
            resetdb() 
            lookup_data()
            client.post('/signup', data={
                'username': 'testuser',
                'email': 'test@gmail.com',
                'password': 'password123'
            }, follow_redirects=True)
        yield client

def test_task_priority_integration(client):
    """Verifies that tasks correctly link to the Priority lookup table."""
    client.post('/signin', data={'username or email': 'testuser', 'password': 'password123'})
    client.post('/add_subject', data={'name': 'Math', 'color_id': 1})
    
    with app.app_context():
        # Get the 'high' priority record (usually seeded with weight 1)
        high_prio = Priority.query.filter_by(level='high').first()
        p_id = high_prio.id

    client.post('/add_task', data={
        'title': 'Urgent Revision',
        'subject_id': 1,
        'priority_id': p_id, # Linking the specific ID
        'description': 'Important'
    }, follow_redirects=True)

    with app.app_context():
        task = Task.query.filter_by(title='Urgent Revision').first()
        assert task.priority.level == 'high'
        assert task.priority.weight == 1  # Verifying the logic weight

def test_dashboard_access(client):
    client.post('/signin', data={'username or email': 'testuser', 'password': 'password123'})
    rv = client.get('/dashboard')
    assert rv.status_code == 200
    assert b"welcome" in rv.data.lower()

def test_unauthorized_access(client):
    rv = client.get('/dashboard', follow_redirects=True)
    assert b"sign in" in rv.data.lower()


def test_create_subject_and_membership(client):
    client.post('/signin', data={'username or email': 'testuser', 'password': 'password123'})
    client.post('/add_subject', data={'name': 'Biology', 'color_id': 1}, follow_redirects=True)
    with app.app_context():
        sub = Subject.query.filter_by(name='Biology').first()
        assert sub is not None
        membership = SubjectMember.query.filter_by(subject_id=sub.subject_id).first()
        assert membership.user_id == 1

def test_task_due_date_error_handling(client):
    """Verifies [2026-02-16] instruction: invalid dates are handled as None."""
    client.post('/signin', data={'username or email': 'testuser', 'password': 'password123'})
    client.post('/add_subject', data={'name': 'Math', 'color_id': 1})
    client.post('/add_task', data={
        'title': 'Test Invalid Date',
        'subject_id': 1,
        'priority_id': 1,
        'due_date_str': 'invalid-format'
    }, follow_redirects=True)
    with app.app_context():
        task = Task.query.filter_by(title='Test Invalid Date').first()
        assert task.due_date is None


def test_description(client):
    client.post('/signin', data={'username or email': 'testuser', 'password': 'password123'})
    client.post('/add_subject', data={'name': 'English', 'color_id': 1})
    desc = "Test long description content."
    client.post('/add_task', data={'title': 'Read', 'description': desc, 'subject_id': 1, 'priority_id': 1})
    with app.app_context():
        task = Task.query.filter_by(title='Read').first()
        assert task.description == desc

def test_message_privacy(client):
    client.post('/signin', data={'username or email': 'testuser', 'password': 'password123'})
    client.post('/add_subject', data={'name': 'Secret', 'color_id': 1})
    client.post('/signup', data={'username': 'hacker', 'email': 'h@h.com', 'password': '123'})
    client.post('/signin', data={'username or email': 'hacker', 'password': '123'})
    rv = client.get('/subject/1', follow_redirects=True)
    assert b"access denied" in rv.data.lower()

def test_subject_deletion(client):
    client.post('/signin', data={'username or email': 'testuser', 'password': 'password123'})
    client.post('/add_subject', data={'name': 'DeleteMe', 'color_id': 1})
    client.get('/delete_subject/1', follow_redirects=True)
    with app.app_context():
        assert db.session.get(Subject, 1) is None
        assert SubjectMember.query.filter_by(subject_id=1).first() is None
def test_subject_invite_flow(client):

    client.post('/signin', data={'username or email': 'testuser', 'password': 'password123'})
    client.post('/add_subject', data={'name': 'Group Project', 'color_id': 1})
    
    with app.app_context():
        sub_id = Subject.query.filter_by(name='Group Project').first().subject_id
    
    client.post('/signup', data={'username': 'collab_user', 'email': 'c@c.com', 'password': '123'})
    client.post('/signin', data={'username or email': 'testuser', 'password': 'password123'})
    client.post(f'/invite_user/{sub_id}', data={'username': 'collab_user'})


    client.post('/signin', data={'username or email': 'collab_user', 'password': '123'})
    rv = client.get('/dashboard')
    
    assert b"group project" in rv.data.lower() 

    with app.app_context():

        membership = SubjectMember.query.filter_by(user_id=2, status='pending').first()
        membership_id = membership.id

    client.get(f'/accept_invite/{membership_id}', follow_redirects=True)

    rv_after = client.get('/dashboard')
    assert b"active tasks" in rv_after.data 

def test_404_not_found(client):
    client.post('/signin', data={'username or email': 'testuser', 'password': 'password123'})

    rv = client.get('/subject/9999')
    assert rv.status_code == 404