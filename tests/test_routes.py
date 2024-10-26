import logging
logger = logging.getLogger(__name__)

def test_login(client):
    logger.info("Starting login test")
    
    # Test login success - follow redirect
    response = client.post('/login', data={
        'username': 'jdoe',
        'password': 'test002'
    })
    assert response.status_code == 302  # Expected redirect status code
    assert response.location == '/dashboard'  # Verify redirect target

    # Test login failure - wrong password
    response = client.post('/login', data={
        'username': 'jdoe',
        'password': 'wrongpassword'
    })
    assert response.status_code == 200  # Login failure should stay on the login page
    assert b"Incorrect password" in response.data
    
    # Test login failure - wrong username and password
    response = client.post('/login', data={
        'username': 'wrongusername',
        'password': 'wrongpassword'
    })
    assert response.status_code == 200  
    assert b"Invalid credentials" in response.data