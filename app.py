import os
from dotenv import load_dotenv
from flask import Flask, session, g
from bson.objectid import ObjectId
from db import db
load_dotenv()
from admin.models import PublicQuestionnaire, PrivateQuestionnaire, Questionnaires

questionnaires = Questionnaires()


def create_app(config_filename):
    app = Flask(__name__)
    app.config.from_pyfile(config_filename)

 
    with app.app_context():
        questionnaires.load_app()

    # App Config
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'

    # Register blueprints
    from admin.manage_questionnaire import manage_questionnaire as manage_questionnaire_blueprint
    app.register_blueprint(manage_questionnaire_blueprint, url_prefix="/admin")

    # from questionnaire.questionnaire import questionnaire as questionnaire_blueprint
    # app.register_blueprint(questionnaire_blueprint, url_prefix="/questionnaire")

    from admin.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from landing.landing import landing as landing_blueprint
    app.register_blueprint(landing_blueprint)

    from admin.manage_submissions import manage_submissions as manage_submissions_blueprint
    app.register_blueprint(manage_submissions_blueprint)

    # Authenticate users 
    @app.before_request
    def load_user():
        user = getattr(g, 'user', None)
        if not user and 'user' in session and session["user"]:
            user = db.users.find_one({'_id': ObjectId(session['user'])})
        g.user = user
    return app

if __name__ == '__main__':
    app = create_app('config/local.py')
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('PORT', 5000))
