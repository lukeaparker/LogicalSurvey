import os
import json
import ast
import uuid
import sys
from flask import Flask, render_template, request, redirect, url_for, session, Blueprint, current_app, g
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
from os.path import join, dirname, realpath
from config import *
from utils import restricted
from db import db


manage_submissions = Blueprint(
        'manage_submissions', __name__, template_folder='templates', static_folder='static'
    )


@manage_submissions.route('/admin/manage-submissions')
@restricted(access_level='admin')
def manage_submissions_index():
    """View submissions from shepherde questionnaire."""
    submissions = db.submissions.find()
    results = []
    for submission in submissions:
        res = {
            "ID": submission['_id'],
            "email":submission['email'],
            "referrals": submission['referral_count']
        }
        results.append(res)
    print(results)  
    return render_template('manage_submissions/manage-submissions.html', submissions=results)

@manage_submissions.route('/admin/manage-submissions/view/<submission_id>')
@restricted(access_level='admin')
def view_submissions(submission_id):
    """View submissions from shepherde questionnaire."""
    query = {'_id': ObjectId(submission_id)}
    submission = db.submissions.find_one(query)
    print(submission)
    sys.stdout.flush()
    return render_template('manage_submissions/view-submission.html', submission=submission, id=ObjectId(submission_id))


@manage_submissions.route('/admin/manage-submissions/delete/<submission_id>', methods=['POST'])
@restricted(access_level='admin')
def delete_submissions(submission_id):
    """Delete submission."""
    query = {'_id': ObjectId(submission_id)}
    submission = db.submissions.find_one_and_delete(query)
    return redirect('/admin/manage-submissions')


@manage_submissions.route('/admin/manage-submissions/add-note/<submission_id>', methods=['POST'])
@restricted(access_level='admin')
def add_note(submission_id):
    """Add note to submission."""
    query = {'_id': ObjectId(submission_id)}
    note = request.form.get('note')
    submission = db.submissions.find_one(query)
    db.submissions.update_one(query, {'$push': {'notes' : note }})
    return redirect('/admin/manage-submissions/view/' + submission_id)
