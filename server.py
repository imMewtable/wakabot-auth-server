import model
import requests
import os

from flask import Flask, flash, request, redirect, url_for
from dotenv import load_dotenv


app = Flask(__name__)

load_dotenv('secrets.env')
WAKA_APP_ID = os.getenv('WAKA_APP_ID')
WAKA_APP_SECRET = os.getenv('WAKA_APP_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')


@app.route('/authenticate', methods=['GET'])
def authenticate():
    token = request.args.get('code')
    state = request.args.get('state')
    if model.state_exists(state):
        entry = model.get_user_data_from_state(state)
        token_response = get_first_token_response(token)

        headers = {'Accept': 'application/x-www-form-urlencoded',
                   'Authorization': 'Bearer {}'.format(token_response['access_token'])}
        response = requests.get('https://wakatime.com/api/v1/users/current', headers=headers)

        if response.status_code == 200:
            user_data = response.json()['data']
            username = user_data['username']
            if model.create_user_data(entry.discord_username, username, token_response['access_token'],
                                      token_response['refresh_token'], entry.server_id):
                return redirect(url_for('home'))

            return {'code': 400, 'error': 'user was probably already created'}, 400

            return {'code': 400, 'error': 'wakatime did not respond with success; try again later'}, 400

    return {'code': 400, 'error': 'state was invalid'}, 400


@app.route('/home', methods=['GET'])
def home():
    return "If you're seeing this, authenticating worked! :)"


def get_first_token_response(token):
    headers = {'Accept': 'application/x-www-form-urlencoded'}
    data = {'client_id': WAKA_APP_ID,
            'client_secret': WAKA_APP_SECRET,
            'code': token,
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI}

    response = requests.post(url='https://wakatime.com/oauth/token', data=data, headers=headers)
    return __parse_raw_response__(response.text)


def __parse_raw_response__(response_text):
    # keys and values are separated with & signs
    response_objects = response_text.split('&')
    parsed_response = {}
    for entry in response_objects:
        # split at = to get proper key/value
        kv = entry.split('=')
        parsed_response[kv[0]] = kv[1]

    return parsed_response
