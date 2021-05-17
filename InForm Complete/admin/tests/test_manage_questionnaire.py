import pytest
from admin.models import Questionnaire
from conftest import *
from app import create_app
from db import db
import pymongo
from auth.tests.test_auth import test_login



def test_manage_questionnaire(test_client):
    """Access manage questionnaire route.""" 
    
    # Access denyed 
    response = test_client.get('/admin/manage-questionnaire')
    
    assert response.status_code == 302

    # Access granted 
    test_login(test_client)

    # Login success 
    response = test_client.get('/admin/manage-questionnaire')
    
    assert response.status_code == 200
    assert b"Publish" in response.data


def test_create_question(test_client):
    """Create questions."""


    # Fail to grant access to create questions
    response = test_client.get('/admin/manage-questionnaire/create-question/main/multiple_choice')
    assert response.status_code == 302


    # Authenticate 
    test_login(test_client)

    # Multiple choice 
    response = test_client.get('/admin/manage-questionnaire/create-question/main/multiple_choice')
    assert response.status_code == 302

    # Create question
    # 'yes-no', 'user_input', 'multiple_choice', 'statement'
    
    # Yes-no
    response = test_client.get('/admin/manage-questionnaire/create-question/1/yes-no')
    assert response.status_code == 302

    # User input 
    response = test_client.get('/admin/manage-questionnaire/create-question/1/user_input')
    assert response.status_code == 302

    # Statement  
    response = test_client.get('/admin/manage-questionnaire/create-question/1/statement')
    assert response.status_code == 302

def test_edit_question(test_client):
    """Edit questions."""


    mimetype = 'application/json'
    headers = {
        'Content-Type': mimetype,
        'Accept': mimetype
    }
    data = {
        'Data': [20.0, 30.0, 401.0, 50.0],
        'Date': ['2017-08-11', '2017-08-12', '2017-08-13', '2017-08-14'],
        'Day': 4
    }

    response = test_client.get('/admin/manage-questionnaire/create-question/main/multiple_choice')

