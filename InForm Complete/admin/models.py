import os
import re
import uuid
from flask import session, current_app
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
from os.path import join

valid_subquestions = ['yes-no', 'user_input', 'multiple_choice', 'statement']

# Session Keys
CACHED_QUESTIONNAIRE = 'cached_questionnaire'

class PublicQuestionnaire():
    def __init__(self, db):
        """Init questionnaire class."""
        self.db = db
        self.questionnaire = db.public_questionnaire
        self.logic_jumps = db.public_logic_jumps

    def publish(self, private_questionniare):
        """Updates the public questionnaire with the given questionnaire."""
        self.db.public_is_single_page = self.db.private_is_single_page

        self.questionnaire.remove()
        questions = private_questionniare.get_all_questions()
        for question in questions:
            self.questionnaire.update({'rank': question['rank']}, question, upsert=True)

        self.logic_jumps.remove()
        logic_jumps = private_questionniare.logic_jumps.find()
        for logic_jump in logic_jumps:
            self.logic_jumps.insert_one(logic_jump)

class PrivateQuestionnaire():

    def __init__(self, db):
        """Init questionnaire class."""
        self.db = db
        self.questionnaire = db.private_questionnaire
        self.logic_jumps = db.private_logic_jumps
        
        questionnaire_settings = list(db.questionnaire_settings.find())
        questionnaire_settings = questionnaire_settings[0] if len(
            questionnaire_settings) > 0 else None
        self.is_single_page = questionnaire_settings['is_single_page']

    def get_question_by_id(self, question_id):
        query = {'_id': ObjectId(question_id)}
        return self.questionnaire.find_one(query)

    def get_question_by_rank(self, question_rank):
        """Returns the question document with the given rank"""
        return self.questionnaire.find_one({'rank': question_rank})

    def get_all_questions(self):
        """Query all private questions."""
        results = self.questionnaire.find().sort([('rank', 1)]).collation({'locale': "en_US", 'numericOrdering': True})
        return results

    def get_all_toplevel_questions(self):
        """Query all toplevel private questions."""
        query = {'$or': [{'group': ''}, {'qtype': 'question-group'}]}
        return self.questionnaire.find(query).sort([('rank', 1)]).collation({'locale': "en_US", 'numericOrdering': True})

    def get_all_group_questions(self, group_id):
        """Query all group private questions."""
        query = {'group': group_id}
        results = self.questionnaire.find(query).sort(
            [('rank', 1)]).collation({'locale': "en_US", 'numericOrdering': True})
        return results

    def get_all_question_logic_jumps(self, question_id):
        """Gets all the logic jumps connected to question with the given id"""
        return self.logic_jumps.find({'question_id': question_id})

    def create_question(self, group_id, qtype):
        """Creates a new quesion document in the questionnarie collection."""
        question_group = group_id if group_id != 'main' and qtype in valid_subquestions else ''
        question_group = 'INVALID' if qtype == 'question-group' else question_group
        question_rank = self.questionnaire.count(
            {'$or': [{'group': ''}, {'qtype': 'question-group'}]})
        question = {
            'qtype': qtype,
            'rank': str(question_rank + 1),
            'group': question_group,
            'question_reference': '',
            'input_field_type': '',
            'filename': '',
            'substatement': '',
            'text': '',
            'multiple_choices': [],
            'multi_select': '',
            'multi_choice_type': '',
            'value': '',
            'preset': False
        }
        return self.questionnaire.insert_one(question).inserted_id

    def update_question(self, question_id, request):
        query = {"_id": ObjectId(question_id)}
        question = self.questionnaire.find_one(query)
        rank, qtype, group = question['rank'], question['qtype'], question['group']
        
        filename = self.save_image(request)
        if filename != '' and question['filename']:
            os.remove(current_app.config['FILE_SAVE_PATH'] + question['filename'])
        elif filename == '':
            filename = question['filename']

        multiple_choices = []
        if qtype == 'multiple_choice':
            for choice in question['multiple_choices']:
                choice_id = choice['id']
                choice = {
                    'id': choice_id, 
                    'text': request.form.get(choice_id)
                }
                multiple_choices.append(choice)

        updated_question = {
            'qtype': qtype,
            'rank': rank,
            'group': group,
            'filename': filename,
            'question_reference': request.form.get('question-reference'),
            'input_field_type': request.form.get('input_field_type'),
            'substatement': request.form.get('substatement'),
            'text': request.form.get('question-text'),
            'multiple_choices': multiple_choices,
            'multi_select': question['multi_select'],
            'multi_choice_type': request.form.get('multi_choice_type'),
            'value': request.form.get('value'),
            'preset': False
        }
        self.questionnaire.update_one(
            query, {'$set': updated_question})

    def toggle_type(self, question_id):
        query = {"_id": ObjectId(question_id)}
        question = self.questionnaire.find_one(query)
        updated_question = question
        updated_question['multi_select'] = not updated_question['multi_select']
        self.questionnaire.update_one(query, {'$set': updated_question})

    def delete_question(self, question_id):
        query = {'_id': ObjectId(question_id)}
        question = self.questionnaire.find_one(query)
        if question['qtype'] == 'question-group':
            query = {'group': question_id}
            self.questionnaire.delete_many(query)

        self.questionnaire.delete_one(query)

        for logic_jump in self.get_all_question_logic_jumps(question_id):
            jump_query = {'_id': ObjectId(logic_jump['_id'])}
            self.logic_jumps.delete_one(jump_query)

        for logic_jump in self.logic_jumps.find({'jumps_to': question_id}):
            jump_query = {'_id': ObjectId(logic_jump['_id'])}
            self.logic_jumps.delete_one(jump_query)

        if question['group'] != '' and question['qtype'] != 'question-group':
            self.update__group_ranks(question['group'])
        else:
            self.update_main_ranks()

    def add_question_logic_jump(self, question_id):
        """Creates a logic jump for a given question"""
        query = {'_id': ObjectId(question_id)}
        question = self.questionnaire.find_one(query)

        default_condition = {
            'id': str(uuid.uuid4()), 
            'question_id': '', 
            'eval': 'is', 
            'value': '', 
            'next': ''
        }

        logic_jump = {
            'question_id': question_id,
            'conditions': [default_condition], 
            'jumps_to': ''
        }
        self.logic_jumps.insert_one(logic_jump)
        
    def update_logic_jump(self, jump_id, request):
        """Updates a logic jump document with the given data"""
        query = {'_id': ObjectId(jump_id)}
        logic_jump = self.logic_jumps.find_one(query)
       
        conditions = []
        for condition in logic_jump['conditions']:
            condition_id = condition['id']
            new_condition = {
                'id': condition_id, 
                'question_id': request.form.get(f'{condition_id}-question'), 
                'eval': request.form.get(f'{condition_id}-eval'), 
                'value': request.form.get(f'{condition_id}-value'), 
                'next': request.form.get(f'{condition_id}-next')
            }
            conditions.append(new_condition)

        update_query = {
            '$set': {
                'conditions': conditions, 
                'jumps_to': request.form.get(f'{jump_id}-jumps-to')
            }
        }
        jump = self.logic_jumps.update_one(query, update_query)

    def add_logic_jump_condition(self, jump_id):
        """Adds an empty condition to a logicjump"""
        query = {'_id': ObjectId(jump_id)}
        condition = {'id': str(uuid.uuid4()), 'question_id': '', 'eval': 'is', 'value': '', 'next': ''}
        update_query = {'$push': {'conditions': condition}}
        self.logic_jumps.update_one(query, update_query)

    def delete_logic_jump_condition(self, jump_id, condition_id):
        """Adds an empty condition to a logicjump"""
        query = {'_id': ObjectId(jump_id)}
        update_query = {'$pull': {'conditions': {'id': condition_id}}}
        self.logic_jumps.update_one(query, update_query)

    def delete_logic_jump(self, jump_id):
       """Deletes the logic jump with the given id"""
       self.logic_jumps.delete_one({'_id': ObjectId(jump_id)})

     ### Helper functions ###

    def count_all_toplevel_questions(self):
        """Counts the number of questions not a part of a group"""
        query = {'$or': [{'group': ''}, {'qtype': 'question-group'}]}
        return self.questionnaire.count(query)

    def count_group_subquestions(self, group_id):
        """Counts the number of questions with group set the the given group id"""
        return self.questionnaire.count({'group': group_id})

    def eval_logic_jump(self, jump_id):
        """Evaluates a logic jump to determin if it's jump to should be used"""
        logic_jump = self.logic_jumps.find_one({'_id': ObjectId(jump_id)})
        conditions = logic_jump['conditions']

        input_string = ''
        for condition in conditions:
            question_answer = session['cached_questionnaire'][condition['question_id']]
            answer_variable = re.sub('[^a-zA-Z]', '', question_answer)
            value_vaiable = re.sub('[^a-zA-Z]', '', condition["value"])
            condition_str = f'{answer_variable} {condition["eval"]} {value_vaiable} '
            if condition['next']:
                condition_str += f'{condition["next"]} '
            input_string += condition_str

        allowed_names = {}
        for condition in conditions:
            if condition['eval'] != 'is' and condition['eval'] != 'is not':
                allowed_names[condition['eval']: eval(condition['eval'])]
            value_vaiable = re.sub('[^a-zA-Z]', '', condition["value"])
            allowed_names[value_vaiable] = condition['value']
            question_answer = session['cached_questionnaire'][condition['question_id']]
            answer_variable = re.sub('[^a-zA-Z]', '', question_answer)
            allowed_names[answer_variable] = question_answer

        return self.eval_condition(input_string, allowed_names)

    def eval_condition(self, input_string, allowed_names):
         code = compile(input_string, "<string>", "eval")
         for name in code.co_names:
             if name not in allowed_names:
                 raise NameError(f"Use of {name} not allowed")
         return eval(code, {"__builtins__": {}}, allowed_names)

    def update__group_ranks(self, group_id):
        group = self.questionnaire.find_one(
            {'_id': ObjectId(group_id)})
        subquestions = self.get_all_group_questions(group_id)
        rank = 0
        for question in subquestions:
            question_rank = f'{group["rank"]}{chr(rank + 97)}'
            self.questionnaire.update_one({'_id': question['_id']}, {
                '$set': {'rank': question_rank}})
            rank += 1

    def update_main_ranks(self):
        """Update main ranks."""
        questions = self.get_all_toplevel_questions()
        rank = 0
        for question in questions:
            rank += 1
            query = {"_id": question['_id']}
            entry = {"$set": {"rank": str(rank)}}
            self.questionnaire.update_one(query, entry)
            if question['qtype'] == 'question-group':
                self.update__group_ranks(str(question['_id']))

    def allowed_file(self, filename):
        """Checks that the filetype is an allowed type"""
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in ['jpg', 'png', 'svg', 'jpeg']

    def save_image(self, request):
        """Saves the images to Flask's filesystem"""
        file = None
        if 'question-image' in request.files:
            file = request.files['question-image']
        if file and file.filename == '':
            file = None

        filename = ''
        if file and self.allowed_file(file.filename):
            filename = f'{str(uuid.uuid4())}.{file.filename.rsplit(".", 1)[1].lower()}'
            file.save(os.path.join(current_app.config['FILE_SAVE_PATH'], filename))
        return filename

    def delete_image(self, question_id):
        """Deletes the given image from the document and filestorage"""
        question = self.get_question_by_id(question_id)
        if question['filename']:
            os.remove(current_app.config['FILE_SAVE_PATH'] + question['filename'])
            self.questionnaire.update_one({'_id': ObjectId(question_id)}, {'$set': {'filename': ''}})

    def save_questionnaire_answer(self, question_reference, question_id, answer):
        """Caches the question into the cookie session"""
        questionnaire = session['cached_questionnaire']
        
        questionnaire[question_id] = answer
        session['cached_questionnaire'] = questionnaire

        if question_reference:
            references = session['cached_references']
            references[question_reference] = answer
            session['cached_references'] = references

    def parse(self, text):
        references = session['cached_references']
        new_string = text
        for key in references:
            if type(references[key]) == list:
                if len(references[key]) != 1: 
                    all_but_last = ', '.join(references[key][:-1])
                    last = references[key][-1]
                    new_string = new_string.replace(key, ' and '.join([all_but_last, last])) 
                else:
                    new_string = new_string.replace(key, references[key][0])
            if key in new_string:
                str(new_string)
                new_string = new_string.replace(key, references[key])
        return new_string