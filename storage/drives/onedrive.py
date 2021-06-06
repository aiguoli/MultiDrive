import requests


graph_url = 'https://graph.microsoft.com/v1.0'
login_base_url = 'https://login.microsoftonline.com'
login_code_url = '/common/oauth2/v2.0/authorize'
login_token_url = '/common/oauth2/v2.0/token'

list_dir_url = '/me/drive/root:{path}:/children'
file_url = '/me/drive/root:{path}'

headers = {'Content-Type': 'application/x-www-form-urlencoded'}


def get_login_code(client_id, redirect_uri):
    auth_data = {
        'scope': 'https://graph.microsoft.com/files.readwrite.all offline_access',
        'response_type': 'code',
        'redirect_uri': redirect_uri,
        'client_id': client_id
    }
    response = requests.get(login_base_url + login_code_url, params=auth_data)
    return response.url


def get_login_token(code, client_id, client_secret):
    token_data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'authorization_code',
        'redirect_uri': 'http://localhost:8000/callback',
        'code': code
    }
    response = requests.post(login_base_url+login_token_url, headers=headers, data=token_data).json()
    return response


def refresh_token(token, client_id, client_secret):
    token_data = {
        'client_id': client_id,
        'redirect_uri': 'http://localhost:8000/callback',
        'client_secret': client_secret,
        'refresh_token': token,
        'grant_type': 'refresh_token'
    }
    response = requests.post(login_base_url+login_token_url, headers=headers, data=token_data).json()
    return response


def list_files(token, path):
    url = graph_url + list_dir_url.format(path=path)
    auth_headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
    }
    response = requests.get(url, headers=auth_headers).json()
    return response


def get_file(token, path):
    url = graph_url + file_url.format(path=path)
    auth_headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
    }
    response = requests.get(url, headers=auth_headers).json()
    return response
