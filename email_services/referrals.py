import os
import sys
import requests
import json
from flask import Flask, render_template, request, redirect, url_for, session, Blueprint, current_app, g
from flask_mail import Mail, Message

from app import create_app
from email_services.hash_email import generate_referral_url, unhash_email

referrals = Blueprint(
    'referrals', __name__, template_folder='templates'
    )

mail = Mail(create_app('config/local.py'))

checked_emails = dict()

@referrals.route('/send-referrals', methods=['POST'])
def send_referrals():
    # get the referrers email from the cache
    referrer = session['cached_references']['email']
    # get the encoded url
    referral_url = generate_referral_url(referrer)

    # get the list of emails from the client
    emails = request.form["referrals"].replace(" ", "").split(",")
  
    # instantiate a list for all the failed email attempts
    failed = []

    # header for the API call
    header = {
        'Authorization': 'bearer {}'.format("4580ef5c-807e-4af3-a292-e4d38e3ffd0f")
    }
    # for each email
    for email in emails:
        # checks if the email is in the cache of checked emails
        if email in checked_emails:
            # If it is and the email is known to be invalid or unknown, append it to the failed list
            if checked_emails[email] == 'unknown' or checked_emails[email] == 'invalid':
                failed.append(email)
        # else call the email validation API to validate the email
        else: 
            response = requests.get("https://isitarealemail.com/api/email/validate?email="+email, headers=header)
            result = json.loads(response.content.decode())
            # Add the email to the cache of checked emails
            checked_emails[email] = result['status']

            # check if the email is invalid or unknown, if it is, append it to the failed list
            if result['status'] == 'unknown' or result['status'] == 'invalid':
                failed.append(email)
    # if there are failed emails, return all the emails that failed to be listed clientside
    if len(failed) > 0:
        return {"failed": failed, 'success': False}

    # send the referrals, if there are no invalid emails
    msg = Message('Hello', sender = 'shepherdeintake@gmail.com', recipients = emails)
    msg.body = "Hello! Here's your referral link... " + referral_url
    mail.send(msg)

    return {'success': True, "failed": failed}

@referrals.route('/referred/<hashed>')
def referred_route(hashed):
    session['referral'] = hashed
    
    return redirect(url_for('landing.landing_page'))
