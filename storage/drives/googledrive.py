import requests
import json

base_url = 'https://accounts.google.com/o/oauth2/v2/auth'
auth_url = 'https://accounts.google.com/o/oauth2/v2/auth'

client_id = '216440066284-4rc0jvuh02q8hfd5fgev4ris01rqq8ei.apps.googleusercontent.com'
client_secret = '5RIx-WERt77b2OD_DDXZDBju'


def get_login_code(client_id, redirect_uri):
    auth_data = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'https://www.googleapis.com/auth/drive.file',
        'access_type': 'offline',
        'state': 'sth that could be converted'
    }
    response = requests.get(auth_url, params=json.dumps(auth_data)).json()
    print(response)
    return response


get_login_code(client_id, client_secret)
