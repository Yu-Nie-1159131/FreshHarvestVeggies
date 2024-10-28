from app import db
from app.models import Staff
from app.utility import hashing
from datetime import datetime

def test_staff_login(client, app):
   with app.app_context():
       # Create a test employee account
       test_staff = Staff(
           username='staff_user',
           password=hashing.hash_value('test002', salt='neal'),
           first_name='Test',
           last_name='Staff',
           dept_name='Test Department',
           date_joined=datetime.now()
       )
       db.session.add(test_staff)
       db.session.commit()

       # Test successful login
       response = client.post('/staff/login', data={
           'username': 'staff_user',
           'password': 'test002'
       })
       assert response.status_code == 302  # Should redirect
       assert response.location == '/staff/dashboard'  # Check redirection target

       # Test password error
       response = client.post('/staff/login', data={
           'username': 'staff_user',
           'password': 'wrongpassword'
       })
       assert response.status_code == 200
       assert b"Incorrect password. Please try again." in response.data

       # Test if the username does not exist
       response = client.post('/staff/login', data={
           'username': 'nonexistent_user',
           'password': 'test002'
       })
       assert response.status_code == 200
       assert b"Invalid credentials. Please try again." in response.data

       # Test GET request - should return the login page
       response = client.get('/staff/login')
       assert response.status_code == 200
       assert b'<form' in response.data  

def test_staff_login_session(client, app):
   """Test the session after login"""
   with app.app_context():
       # Create a test employee account
       test_staff = Staff(
           username='staff_user',
           password=hashing.hash_value('test002', salt='neal'),
           first_name='Test',
           last_name='Staff',
           dept_name='Test Department',
           date_joined=datetime.now()
       )
       db.session.add(test_staff)
       db.session.commit()

       # log in
       client.post('/staff/login', data={
           'username': 'staff_user',
           'password': 'test002'
       })

       # Access the session using the test client
       with client.session_transaction() as session:
           assert 'staff_id' in session
           assert 'staff_username' in session
           assert session['staff_username'] == 'staff_user'

def test_staff_dashboard_access(client, app):
   """Test access to dashboard when not logged in"""
   response = client.get('/staff/dashboard', follow_redirects=True)
   assert b'login' in response.data.lower()  # Should redirect to login page

def test_missing_form_fields(client, app):
   """Test form fields missing"""
   # Test for missing username
   response = client.post('/staff/login', data={
       'password': 'test002'
   })
   assert response.status_code == 400  # or other error status codes
   
   # Test for missing password
   response = client.post('/staff/login', data={
       'username': 'staff_user'
   })
   assert response.status_code == 400  # or other error status codes

def test_staff_logout(client, app):
   """If there is a logout function, test the logout"""
   with app.app_context():
       # Create and log in a test user
       test_staff = Staff(
           username='staff_user',
           password=hashing.hash_value('test002', salt='neal'),
           first_name='Test',
           last_name='Staff',
           dept_name='Test Department',
           date_joined=datetime.now()
       )
       db.session.add(test_staff)
       db.session.commit()

       # log in
       client.post('/staff/login', data={
           'username': 'staff_user',
           'password': 'test002'
       })

       # logout
       response = client.get('/staff/logout', follow_redirects=True)
       assert response.status_code == 200

       # Verify that the session has been cleared
       with client.session_transaction() as session:
           assert 'staff_id' not in session
           assert 'staff_username' not in session