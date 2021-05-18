import os
import bcrypt
import uuid
import argparse

from pymongo import MongoClient
from flask import Flask, current_app


class MongDB(): 

    def __init__(self): 
        uri = os.environ.get('DB_URI', 'mongodb://root:AVeryStrongPassword1234@mongo:27017/Shepherde?authSource=admin')
        client = MongoClient(uri)
        self.db = client.get_default_database()

    def load_app(self):
        if current_app.config['DATABASE'] != 'test':
            self.public_questionnaire = self.db.public_questionnaire
            self.private_questionnaire = self.db.private_questionnaire
            self.questionnaire_settings = self.db.questionnaire_settings
            self.public_logic_jumps = self.db.public_logic_jumps
            self.private_logic_jumps = self.db.private_logic_jumps
            self.submissions = self.db.submissions 
            self.users = self.db.users
            self.preload()
        else:
            # Init test database 
            self.public_questionnaire = self.db.public_questionnaire_test
            self.private_questionnaire = self.db.private_questionnaire_test
            self.questionnaire_settings = self.db.questionnaire_settings
            self.public_logic_jumps = self.db.public_logic_jumps_test
            self.private_logic_jumps = self.db.private_logic_jumps_test
            self.submissions = self.db.submissions_test
            self.users = self.db.users_test
            self.preload()

    def preload(self):
        admin = {
            'email': 'admin@zeta-apps.com',
            'password': bcrypt.hashpw('super-secret-password'.encode('utf-8'), bcrypt.gensalt()),
            'access_level': 'admin'
        }
        self.users.update({'email': admin['email']}, admin, upsert=True)
        
        
        name = {
            'qtype': 'user_input',
            'rank': '1',
            'group': '',
            'question_reference': 'name',
            'input_field_type': 'name',
            'filename': '',
            'substatement': 'Please enter your first and last name',
            'text': 'Hello what is your name?',
            'multiple_choices': [],
            'multi_select': '',
            'multi_choice_type': '',
            'value': '',
            'preset': True,
        }
        self.public_questionnaire.update({'question_reference': name['question_reference']}, name, upsert=True)
        self.private_questionnaire.update({'question_reference': name['question_reference']}, name, upsert=True)

        email = {
            'qtype': 'user_input',
            'rank': '2',
            'group': '',
            'question_reference': 'email',
            'input_field_type': 'email',
            'filename': '',
            'substatement': 'Enter your email.',
            'text': 'Hello name! What is your email?',
            'multiple_choices': [],
            'multi_select': '',
            'multi_choice_type': '',
            'value': '',
            'preset': True,
        }
        self.public_questionnaire.update({'question_reference': email['question_reference']}, email, upsert=True)
        self.private_questionnaire.update({'question_reference': email['question_reference']}, email, upsert=True)


        zipcode = {
            'qtype': 'user_input',
            'rank': '3',
            'group': '',
            'question_reference': 'zipcode',
            'input_field_type': 'zipcode',
            'filename': '',
            'substatement': 'Enter your zipcode Code.',
            'text': 'Where are you located?',
            'multiple_choices': [],
            'multi_select': '',
            'value': '',
            'multi_choice_type': '',
            'value': '',
            'preset': True,
        }
        self.public_questionnaire.update({'question_reference': zipcode['question_reference']}, zipcode, upsert=True)
        self.private_questionnaire.update({'question_reference': zipcode['question_reference']}, zipcode, upsert=True)

        sun = {
            'qtype': 'multiple_choice',
            'rank': '4',
            'group': '',
            'question_reference': 'sun',
            'input_field_type': 'sun',
            'filename': '',
            'substatement': 'The amount of sun that the plants will be exposed too.',
            'text': 'How much Sun will your plants get?',
            'multiple_choices': [
                    {
                        'id':str(uuid.uuid4()),
                        'text': "Full Sun",
                        'value': "1"
                    },{
                        'id':str(uuid.uuid4()),
                        'text': "Part Sun",
                        'value': "2"
                    },{
                        'id':str(uuid.uuid4()),
                        'text': "Shade",
                        'value': "3"
                    }
                ],
            'multi_select': '',
            'multi_choice_type': 'short',
            'preset': True,
        }
        self.private_questionnaire.update({'question_reference': sun['question_reference']}, sun, upsert=True)
        self.public_questionnaire.update({'question_reference': sun['question_reference']}, sun, upsert=True)


        size = {
            'qtype': 'multiple_choice',
            'rank': '5',
            'group': '',
            'question_reference': 'size',
            'input_field_type': 'size',
            'filename': '',
            'substatement': 'The size of the plant.',
            'text': 'How large are your plants?',
            'multiple_choices': [
                    {
                        'id':str(uuid.uuid4()),
                        'text': "Small",
                        'value': "1"
                    },{
                        'id':str(uuid.uuid4()),
                        'text': "Medium",
                        'value': "2"
                    },{
                        'id':str(uuid.uuid4()),
                        'text': "Large",
                        'value': "3"
                    }
                ],
            'multi_select': '',
            'multi_choice_type': 'short',
            'preset': True,
        }
        self.private_questionnaire.update({'question_reference': size['question_reference']}, size, upsert=True)
        self.public_questionnaire.update({'question_reference': size['question_reference']}, size, upsert=True)


        exp = {
            'qtype': 'multiple_choice',
            'rank': '6',
            'group': '',
            'question_reference': 'exp',
            'input_field_type': 'exp',
            'filename': '',
            'substatement': 'How experienced of a grower you are.',
            'text': 'How experienced are you at tending to plants?',
            'multiple_choices': [
                    {
                        'id':str(uuid.uuid4()),
                        'text': "Beginner",
                        'value': "1"
                    },{
                        'id':str(uuid.uuid4()),
                        'text': "Intermediate",
                        'value': "2"
                    },{
                        'id':str(uuid.uuid4()),
                        'text': "Expert",
                        'value': "3"
                    }
                ],
            'multi_select': '',
            'multi_choice_type': 'short',
            'preset': True,
        }
        self.private_questionnaire.update({'question_reference': exp['question_reference']}, exp, upsert=True)
        self.public_questionnaire.update({'question_reference': exp['question_reference']}, exp, upsert=True)


        preferences = {
            'qtype': 'multiple_choice',
            'rank': '7',
            'group': '',
            'question_reference': 'preferences',
            'input_field_type': 'preferences',
            'filename': '',
            'substatement': 'What your favorite types of plants to grow are.',
            'text': 'What plant preferences do you have?',
            'multiple_choices': [
                    {
                        'id':str(uuid.uuid4()),
                        'text': "Fruit",
                        'value': "f"
                    },{
                        'id':str(uuid.uuid4()),
                        'text': "Vegetables",
                        'value': "g"
                    },{
                        'id':str(uuid.uuid4()),
                        'text': "Herbs",
                        'value': "h"
                    },{
                        'id':str(uuid.uuid4()),
                        'text': "Flowers",
                        'value': "i"
                    }
                ],
            'multi_select': True,
            'multi_choice_type': 'short',
            'preset': True,
        }
        self.private_questionnaire.update({'question_reference': preferences['question_reference']}, preferences, upsert=True)
        self.public_questionnaire.update({'question_reference': preferences['question_reference']}, preferences, upsert=True)


        settings = {
            'heading': 'Thanks for applying!',
            'summary': 'Thank you for taking the time to submit an application!',
            'is_single_page': True
        }
        self.questionnaire_settings.update({'heading': settings['heading']}, settings, upsert=True)


db = MongDB()