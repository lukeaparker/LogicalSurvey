from flask import render_template, redirect, session, abort, g, url_for
from functools import wraps


def restricted(access_level, redirect_to='/'):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if g.user is None or not g.user['access_level'] == access_level:
                return redirect(redirect_to)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def save_questionnaire_answer(question_reference, answer):
    """Caches the question into the cookie session"""
    questionnaire = session['cached_questionnaire']
    questionnaire[question_reference] = answer
    session['cached_questionnaire'] = questionnaire

