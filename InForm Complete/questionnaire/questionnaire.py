import os
import sys

from flask import Blueprint, session, redirect
from flask import render_template, request
from utils import save_questionnaire_answer
from questionnaire.models import PublicQuestionnaire
from db import db

public_questionnaire = PublicQuestionnaire(db)
questionnaire = Blueprint('questionnaire', __name__, template_folder='templates', static_folder='static')

@questionnaire.route('/')
def determine_rank():
    questionnaire_settings = list(db.questionnaire_settings.find())
    questionnaire_settings = questionnaire_settings[0] if len(
        questionnaire_settings) > 0 else None

    if questionnaire_settings['is_single_page']:
        return redirect('/questionnaire/single')

    if session.get("last_question_rank"):
        return redirect("/questionnaire/"+ str( int(session["last_question_rank"]) + 1))
    else:
        return redirect("/questionnaire/1")

@questionnaire.route('/<rank>')
def question_view(rank):
    """Renders the question view for a question with the given rank or redirects to the results page"""
    question = public_questionnaire.get_question_by_rank(rank)
    if rank.isnumeric() and int(rank) == 1:
        # Create the questionnarie cache to save the questions answers
        session['cached_questionnaire'] = {}
        session['cached_references'] = {}
        # session['cached_questionnaire_text'] = {}
        session['cached_responses'] = []
        session['last_question_rank']  = 0


    total_questions = public_questionnaire.count_all_toplevel_questions()
    if rank.isnumeric() and int(rank) > total_questions:
        return redirect('/questionnaire/results')

    # image_url = os.path.join(FILE_GET_PATH, question['filename'])

    question_text = public_questionnaire.parse(question['text'])
    return render_template('questionnaire/questionnaire.html', question_text=question_text, question=question)

@questionnaire.route('/single')
def questionnaire_single_page_preview_view():
    """Admin preview question."""

    # Create the questionnarie cache to save the questions answers
    session['cached_questionnaire'] = {}
    session['cached_references'] = {}
    session['cached_responses'] = []

    questions = list(public_questionnaire.get_all_toplevel_questions())
    subquestions = []
    for question in questions:
        subquestions.append(list(public_questionnaire.get_all_group_questions(str(question['_id']))))

    return render_template('questionnaire/single-page.html',
        questions=zip(questions, subquestions))


@questionnaire.route('/record/<question_id>', methods=['POST'])
def question_controller(question_id):
    """Save the question with the given id's answer to the cache."""

    question = public_questionnaire.get_question_by_id(question_id)

    session['last_question_rank'] = question["rank"]

    answer = request.form.getlist('question-answer') if question['multi_select'] else request.form.get('question-answer')
    if question['qtype'] != 'statement' and question['qtype'] != 'question-group':
        response = {
            "question_text": question['text'],
            "value": answer
        }
        print(len(session["cached_responses"]), question["rank"])
        sys.stdout.flush()
        if len(session["cached_responses"]) >= int(question["rank"]):
            session["cached_responses"][int(question["rank"])-1] = response
        else:
            session["cached_responses"].append(response)
        public_questionnaire.save_questionnaire_answer(question['question_reference'], question_id, answer)
 
    next_rank = int(question["rank"]) + 1 if question['rank'].isnumeric() else ''
    if question['qtype'] == 'question-group':
        total_subquestions = public_questionnaire.count_group_subquestions(str(question['_id']))
        if total_subquestions > 0:
            next_rank = f'{question["rank"]}a'
    elif not question['rank'].isnumeric():
        subq_index = ord(question['rank'][len(question['rank'])-1]) - 97
        group = public_questionnaire.get_question_by_id(question['group'])
        parent_rank = question['rank'][:len(question['rank'])-1]

        total_subquestions = public_questionnaire.count_group_subquestions(str(group['_id']))
        if subq_index + 1 >= total_subquestions:
            next_rank = f'{int(parent_rank) + 1}'
        else:
            next_rank = f'{parent_rank}{chr(subq_index + 1 + 97)}'

    logic_jumps = public_questionnaire.get_all_question_logic_jumps(question_id)
    for logic_jump in logic_jumps:
        if public_questionnaire.eval_logic_jump(logic_jump['_id']):
            if logic_jump['jumps_to'] != '-1':
                next_rank = public_questionnaire.get_question_by_id(logic_jump["jumps_to"])['rank']
            else:
                next_rank = '-1'
            break
        
    return redirect(f'/questionnaire/{next_rank}')


@questionnaire.route('/record-single-page', methods=['POST'])
def single_page_questionnaire_controller():
    for question_id in request.form.keys():
        question = public_questionnaire.get_question_by_id(question_id)
        if question:
            answer = request.form.getlist(question_id) if question['multi_select'] else request.form.get(question_id)
            response = {
                "question_text": question['text'],
                "value": answer
            }
            sys.stdout.flush()
            if len(session["cached_responses"]) >= int(question["rank"]):
                session["cached_responses"][int(question["rank"])-1] = response
            else:
                session["cached_responses"].append(response)
            public_questionnaire.save_questionnaire_answer(question['question_reference'], question_id, answer)
        else:
            print("Issue occured while recording question answer.")
    return redirect('/questionnaire/results')


@questionnaire.route('/results')
def results():
    """Render results of questionnaire."""
    if not session.get("last_question_rank") and public_questionnaire.is_single_page is False:
        return redirect('/questionnaire')
    
    if session.get("last_question_rank"):
        del session["last_question_rank"]
    
    preview_result_templates = list(db.questionnaire_settings.find())
    preview_result_template = preview_result_templates[0] if len(
        preview_result_templates) > 0 else None
    parsed_template = {
        'heading': public_questionnaire.parse(preview_result_template['heading']),
        'summary': public_questionnaire.parse(preview_result_template['summary'])
    }

    submission = {
        "email": session['cached_references']['email'],
        "name": session['cached_references']['name'],
        "zipcode": session['cached_references']['zipcode'],
        "sun": session['cached_references']['sun'],
        "exp": session['cached_references']['exp'],
        "size": session['cached_references']['size'],
        "preferences": session['cached_references']['preferences'],
        "responses": session['cached_responses'],
        "notes": list()
    }

    db.submissions.update({"email": submission['email']}, submission, upsert=True)

    return render_template('questionnaire/results.html', results_page=True, preview_result_template=parsed_template)

@questionnaire.route('/success')
def success():
    return render_template("questionnaire/success.html", success_page=True)