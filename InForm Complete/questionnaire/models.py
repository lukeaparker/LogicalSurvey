import os
import re
import sys
from flask import session
from bson.objectid import ObjectId

# Form Validation / Downloads Paths
FILE_SAVE_PATH = 'static/UPLOADS/'
FILE_GET_PATH = 'UPLOADS/'

valid_subquestions = ['yes-no', 'user_input', 'multiple_choice', 'statement']

# Session Keys
CACHED_QUESTIONNAIRE = 'cached_questionnaire'

class PublicQuestionnaire():
    def __init__(self, db):
        """Init questionnaire class."""
        self.questionnaire = db.public_questionnaire
        self.logic_jumps = db.public_logic_jumps

        questionnaire_settings = list(db.questionnaire_settings.find())
        questionnaire_settings = questionnaire_settings[0] if len(
            questionnaire_settings) > 0 else None
        self.is_single_page = questionnaire_settings['is_single_page']

    def get_question_by_id(self, question_id):
        """Return the question document with the given id"""
        return self.questionnaire.find_one({'_id': ObjectId(question_id)})

    def get_question_by_rank(self, question_rank):
        """Returns the question document with the given rank"""
        return self.questionnaire.find_one({'rank': question_rank})

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

    def save_questionnaire_answer(self, question_reference, question_id, answer):
        """Caches the question into the cookie session"""
        question = self.get_question_by_id(question_id)
        
        questionnaire = session['cached_questionnaire']
        questionnaire[question_id] = answer
        session['cached_questionnaire'] = questionnaire

        # questionnaire_text = session['cached_questionnaire_text']
        # key = re.sub('[^a-zA-Z]', '', question['text'])
        # questionnaire_text[key] = answer
        # session['cached_questionnaire_text'] = questionnaire_text

        if question_reference:
            references = session['cached_references']
            references[question_reference] = answer
            session['cached_references'] = references

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

    def count_all_toplevel_questions(self):
        """Counts the number of questions not a part of a group"""
        query = {'$or': [{'group': ''}, {'qtype': 'question-group'}]}
        return self.questionnaire.count(query)

    def count_group_subquestions(self, group_id):
        """Counts the number of questions with group set the the given group id"""
        return self.questionnaire.count({'group': group_id})

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