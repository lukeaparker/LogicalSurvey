import os
from flask import Flask, render_template, request, redirect, url_for, session, Blueprint, current_app, g

# landing = Blueprint('landing', __name__, template_folder='templates', static_folder='static')                         
landing = Blueprint(
    'landing', __name__, template_folder='templates')



@landing.route('/')
def landing_page():
    """Displays landing page"""
    return render_template('landing.html')
