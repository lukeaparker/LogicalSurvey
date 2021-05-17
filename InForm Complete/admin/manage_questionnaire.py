import os
import uuid
from flask import Flask, render_template, request, redirect
from flask import url_for, session, Blueprint, current_app, g
from bson.objectid import ObjectId
from os.path import join
from utils import restricted
from admin.models import PublicQuestionnaire, PrivateQuestionnaire
from db import db


private_questionnaire = PrivateQuestionnaire(db)
public_questionnaire = PublicQuestionnaire(db)
manage_questionnaire = Blueprint('manage_questionnaire', __name__, template_folder='templates', static_folder='static')


@manage_questionnaire.after_request
def after_request_func(response):
    if 'clear_session' in session and session['clear_session']:
        session['clear_session'] = False
        session.clear()
    return response


# View questionnaire
@manage_questionnaire.route('/manage-questionnaire')
@restricted(access_level='admin')
def manage_questionnaire_view():
    """Return questionnaire portal for editing tools."""
    # to clear the questionnaire and logic jump collections uncomment the following line
    # private_questionnaire.questionnaire.remove()
    # private_questionnaire.logic_jumps.remove()
    questions = list(private_questionnaire.get_all_questions())

    results_previews = list(db.preview_results.find())
    results_preview = results_previews[0] if len(
        results_previews) > 0 else None
    return render_template('manage_questionnaire/manage-questionnaire.html', questions=questions,
                           preview_result=results_preview, admin_page=True)


@manage_questionnaire.route('/manage-questionnaire/create-question/<group_id>/<qtype>')
@restricted(access_level='admin')
def create_question(group_id, qtype):
    """Creates a new quesion document in the questionnarie collection."""
    question_id = private_questionnaire.create_question(group_id, qtype)
    return redirect(url_for('manage_questionnaire.manage_questionnaire_view', question_id=question_id))


@manage_questionnaire.route('/manage-questionnaire/update/<question_id>')
@restricted(access_level='admin')
def question_update_view(question_id):
    """Renders the edit view for the quesion with the given _id."""
    question = private_questionnaire.get_question_by_id(question_id)
    if question['qtype'] == 'question-group':
        subquestions = private_questionnaire.get_all_group_questions(question_id)
        questions = list(private_questionnaire.questionnaire.find({'group': ''}))
        return render_template('manage_questionnaire/edit-question.html', question=question, qtype=question['qtype'],
                               questions=questions, subquestions=subquestions)
    questions = list(private_questionnaire.get_all_toplevel_questions())
    image_url = os.path.join(current_app.config['FILE_GET_PATH'], question['filename'])
    return render_template('manage_questionnaire/edit-question.html', question=question, qtype=question['qtype'],
                           questions=questions, image_url=image_url)


@manage_questionnaire.route('/manage-questionnaire/update/<question_id>', methods=['POST'])
@restricted(access_level='admin')
def question_update_controller(question_id):
    """Updates the quesion document with the given is with a new document."""
    private_questionnaire.update_question(question_id, request)
    return redirect(url_for('manage_questionnaire.manage_questionnaire_view'))


@manage_questionnaire.route('/manage-questionnaire/update/<question_id>/delete-image')
@restricted(access_level='admin')
def question_remove_image(question_id):
    """Updates the quesion document with the given is with a new document."""
    private_questionnaire.delete_image(question_id)
    return redirect(url_for('manage_questionnaire.question_update_view', question_id=question_id))


@manage_questionnaire.route('/manage-questionnaire/update/multiple-choice/toggle-type/<question_id>')
@restricted(access_level='admin')
def change_multiple_choice_type_update(question_id):
    """Renders the create question view"""
    private_questionnaire.toggle_type(question_id)
    return redirect(url_for('manage_questionnaire.question_update_view', question_id=question_id))


@manage_questionnaire.route('/manage-questionnaire/update/multiple-choice/add-option/<question_id>')
@restricted(access_level='admin')
def add_multiple_choice_option_update(question_id):
    """Renders the create question view"""
    choice = {'id': str(uuid.uuid4()), 'text': ''}
    query = {'$push': {'multiple_choices': choice}}
    private_questionnaire.questionnaire.update_one(
        {'_id': ObjectId(question_id)}, query)
    return redirect(url_for('manage_questionnaire.question_update_view', question_id=question_id))


@manage_questionnaire.route('/manage-questionnaire/update/multiple-choice/delete-option/<question_id>/<choice>')
@restricted(access_level='admin')
def remove_multiple_choice_option_update(question_id, choice):
    """Renders the create question view"""
    query = {'$pull': {'multiple_choices': {'id': choice}}}
    private_questionnaire.questionnaire.update_one(
        {'_id': ObjectId(question_id)}, query)
    return redirect(url_for('manage_questionnaire.question_update_view', question_id=question_id))


@manage_questionnaire.route('/manage-questionnaire/question-group/add-subquestion/<question_id>/<subquestion_id>')
@restricted(access_level='admin')
def add_question_subquestion(question_id, subquestion_id):
    """Renders the create question view"""
    total_subquestions = private_questionnaire.questionnaire.count({'group': question_id})
    group = private_questionnaire.questionnaire.find_one(
        {'_id': ObjectId(question_id)})
    subquestion_rank = f'{group["rank"]}{chr(total_subquestions + 97)}'
    query = {'_id': ObjectId(subquestion_id)}
    private_questionnaire.questionnaire.update_one(
        query, {'$set': {'group': question_id, 'rank': subquestion_rank}})
    private_questionnaire.update_main_ranks()
    return redirect(url_for('manage_questionnaire.question_update_view', question_id=question_id))


@manage_questionnaire.route('/manage-questionnaire/question-group/remove-subquestion/<question_id>/<subquestion_id>')
@restricted(access_level='admin')
def remove_question_subquestion(question_id, subquestion_id):
    """Renders the create question view"""
    # query = { '$or': [{ 'group': '' }, { 'qtype': 'question-group' }]}
    # total_questions = questionnaire.count(query)
    query = {'_id': ObjectId(subquestion_id)}
    private_questionnaire.questionnaire.update_one(
        query, {'$set': {'group': ''}})
    private_questionnaire.update_main_ranks()
    return redirect(url_for('manage_questionnaire.question_update_view', question_id=question_id))


@manage_questionnaire.route('/manage-questionnaire/update/<question_id>/logic-jump')
@restricted(access_level='admin')
def logic_jump_update_view(question_id):
    """Renders the edit view for the quesion with the given _id."""
    question = private_questionnaire.get_question_by_id(question_id)
    questions = list(private_questionnaire.get_all_questions())
    logic_jumps = list(private_questionnaire.get_all_question_logic_jumps(question_id))
    return render_template('manage_questionnaire/edit-question.html', question=question,
                           questions=questions, logic_jump=True, logic_jumps=logic_jumps)


@manage_questionnaire.route('/manage-questionnaire/update/<question_id>/add-logic-jump')
@restricted(access_level='admin')
def add_question_logic_jump(question_id):
    """Adds a logic jump to the question with the given id"""
    private_questionnaire.add_question_logic_jump(question_id)
    return redirect(url_for('manage_questionnaire.logic_jump_update_view', question_id=question_id))


@manage_questionnaire.route('/manage-questionnaire/update/<question_id>/update-logic-jumps', methods=['POST'])
@restricted(access_level='admin')
def update_question_logic_jumps(question_id):
    """Updates the logic jumps associated with the given question id"""
    for logic_jump in private_questionnaire.get_all_question_logic_jumps(question_id):
        private_questionnaire.update_logic_jump(logic_jump['_id'], request)
    return redirect(url_for('manage_questionnaire.logic_jump_update_view', question_id=question_id))


@manage_questionnaire.route('/manage-questionnaire/update/<question_id>/logic-jump/<jump_id>/remove')
@restricted(access_level='admin')
def remove_question_logic_jump(question_id, jump_id):
    """Renders the create question view"""
    private_questionnaire.delete_logic_jump(jump_id)
    return redirect(url_for('manage_questionnaire.logic_jump_update_view', question_id=question_id))


@manage_questionnaire.route('/manage-questionnaire/update/<question_id>/logic-jump/<jump_id>/add-condition/')
@restricted(access_level='admin')
def app_question_logic_jump_condition(question_id, jump_id):
    """Renders the create question view"""
    private_questionnaire.add_logic_jump_condition(jump_id)
    return redirect(url_for('manage_questionnaire.logic_jump_update_view', question_id=question_id))


@manage_questionnaire.route('/manage-questionnaire/update/<question_id>/logic-jump/<jump_id>/remove-condition/<condition_id>')
@restricted(access_level='admin')
def remove_question_logic_jump_condition(question_id, jump_id, condition_id):
    """Renders the create question view"""
    private_questionnaire.delete_logic_jump_condition(jump_id, condition_id)
    return redirect(url_for('manage_questionnaire.logic_jump_update_view', question_id=question_id))


@manage_questionnaire.route('/manage-questionnaire/delete/<question_id>', methods=['POST'])
@restricted(access_level='admin')
def question_delete_controller(question_id):
    """Delete one question. Reorder the others."""
    private_questionnaire.delete_question(question_id)
    return redirect(url_for('manage_questionnaire.manage_questionnaire_view'))


@manage_questionnaire.route('/manage-questionnaire/preview/<rank>')
@restricted(access_level='admin')
def questionnaire_preview_view(rank):
    """Admin preview question."""
    question = private_questionnaire.get_question_by_rank(rank)
    if rank.isnumeric() and int(rank) == 1:
        # Create the questionnarie cache to save the questions answers
        session['cached_questionnaire'] = {}
        session['cached_references'] = {}

    total_questions = private_questionnaire.count_all_toplevel_questions()
    if (rank.isnumeric() and int(rank) > total_questions) or rank == '-1':
        return redirect('/admin/manage-questionnaire/preview/results')

    image_url = os.path.join(current_app.config['FILE_GET_PATH'], question['filename'])
    question_text = private_questionnaire.parse(question['text'])
    return render_template('manage_questionnaire/preview-questionnaire.html',
                           question_text=question_text, question=question, image_url=image_url)


@manage_questionnaire.route('/manage-questionnaire/preview/record/<question_id>', methods=['POST'])
@restricted(access_level='admin')
def questionnaire_preview_controller(question_id):
    """Save the question with the given id's answer to the cache."""
    question = private_questionnaire.get_question_by_id(question_id)
    
    answer = request.form.getlist('question-answer') if question['multi_select'] else request.form.get('question-answer')
    private_questionnaire.save_questionnaire_answer(question['question_reference'], question_id, answer)
    
    next_rank = int(question["rank"]) + 1 if question['rank'].isnumeric() else ''
    if question['qtype'] == 'question-group':
        total_subquestions = private_questionnaire.count_group_subquestions(str(question['_id']))
        if total_subquestions > 0:
            next_rank = f'{question["rank"]}a'
    elif not question['rank'].isnumeric():
        subq_index = ord(question['rank'][len(question['rank'])-1]) - 97
        group = private_questionnaire.get_question_by_id(question['group'])
        parent_rank = question['rank'][:len(question['rank'])-1]

        total_subquestions = private_questionnaire.count_group_subquestions(str(group['_id']))
        if subq_index + 1 >= total_subquestions:
            next_rank = f'{int(parent_rank) + 1}'
        else:
            next_rank = f'{parent_rank}{chr(subq_index + 1 + 97)}'

    logic_jumps = private_questionnaire.get_all_question_logic_jumps(question_id)
    for logic_jump in logic_jumps:
        if private_questionnaire.eval_logic_jump(logic_jump['_id']):
            if logic_jump['jumps_to'] != '-1':
                next_rank = private_questionnaire.get_question_by_id(logic_jump["jumps_to"])['rank']
            else:
                next_rank = '-1'
            break
        
    return redirect(f'/admin/manage-questionnaire/preview/{next_rank}')


@manage_questionnaire.route('/manage_questionnaire/update-results', methods=['POST'])
def update_results():
    preview_results = db.preview_results
    new_results = {
        'heading': request.form.get('questionnaire-heading'),
        'summary': request.form.get('questionnaire-summary')
    }
    if preview_results.count() == 0:
        preview_results.insert_one(new_results)
    else:
        results = preview_results.find()[0]
        preview_results.update_one(
            {'_id': results['_id']}, {'$set': new_results})
    return redirect(url_for('manage_questionnaire.manage_questionnaire_view'))


@manage_questionnaire.route('/manage-questionnaire/preview/results')
@restricted(access_level='admin')
def preview_results():
    """Render results of questionnaire."""
    preview_result_templates = list(db.preview_results.find())
    preview_result_template = preview_result_templates[0] if len(
        preview_result_templates) > 0 else None
    parsed_template = {
        'heading': private_questionnaire.parse(preview_result_template['heading']),
        'summary': private_questionnaire.parse(preview_result_template['summary'])
    }
    return render_template('questionnaire/results.html', results_page=True, preview_result_template=parsed_template)


@manage_questionnaire.route('/manage-questionnaire/publish', methods=['POST'])
@restricted(access_level='admin')
def publish():
    """Publishes questionnaire."""
    public_questionnaire.publish(private_questionnaire)
    return redirect('/admin/manage-questionnaire')
