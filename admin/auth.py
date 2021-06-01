from flask import Blueprint, render_template, request, flash, redirect, url_for, session
import bcrypt
from db import db
from utils import restricted
import sys

auth = Blueprint('auth', __name__, template_folder='templates')


@auth.route('/admin')
def admin_login():
    if 'user' in session and session['user']:
        return redirect('/admin/manage-questionnaire')
    return render_template('auth/admin-login.html')


@auth.route('/admin/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False
    
    admin = db.users.find_one({'email': email})

    if not admin or not bcrypt.checkpw(password.encode('utf-8'), admin['password']):
        print('Email or password was incorrect, please try agian')
        flash('Email or password was incorrect, please try agian')
        return redirect('/admin')

    if remember:
        session['user'] = str(admin['_id'])
    
    return redirect('/admin')


@auth.route('/logout')
def admin_logout():
    session['user'] = None
    return redirect('/admin')


@auth.route('/admin/create', methods=["GET", "POST"])
@restricted(access_level='admin')
def admin_logadmin_Createout():
    if request.method == "GET":
        return render_template('auth/admin-create.html')
    elif request.method == "POST":
        form = request.form
        
        if form['server-pw'] != "super-secret-server-password":
            return {'failed': "incorrect server password"}
        
        admin = db.users.find_one({'email': form["email"]})

        if admin:
            return {'failed': "An Admin with this email already exists"}

        user = {
                'email': form['email'],
                'password': bcrypt.hashpw(form['password'].encode('utf-8'), bcrypt.gensalt()),
                'access_level': 'admin'
            }

        db.users.insert_one(user)

        return {'failed': ""}

