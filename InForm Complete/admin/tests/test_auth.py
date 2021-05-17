import pytest
from admin.models import Questionnaire
from conftest import *
from app import create_app
from db import db
import pymongo

def test_login_fail(test_client):
    """Test login failure."""
    
    # Login fail
    response = test_client.post('/admin/login',
                                data=dict(email='sparky@jasdfj.tv', password='super-secret-password'),
                                follow_redirects=True)
    assert response.status_code == 200
    assert b"Login" in response.data


    

def test_admin(test_client,):
    """Access admin route.""" 

    # Admin success 
    response = test_client.get('/admin', follow_redirects=True)
    assert response.status_code == 200
    assert b"Login" in response.data

def test_login(test_client):
    """Login successfully to access admin panel.""" 

    # Login success 
    response = test_client.post('/admin/login',
                                data=dict(email='admin@shepherde.com', password='super-secret-password'),
                                follow_redirects=True)
    assert response.status_code == 200
    assert b"Publish" in response.data
    
def test_logout(test_client):
    """Login successfully to redirect to landing.""" 
    
    # Login success 
    test_login(test_client)

    # Logout success 
    response = test_client.get('/logout', follow_redirects=True)
    assert response.status_code == 200


