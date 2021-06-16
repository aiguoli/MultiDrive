import requests
from django.shortcuts import redirect

from storage.utils import get_readme, od_path_attr, generate_breadcrumbs

graph_url = 'https://graph.microsoft.com/v1.0'

login_base_url = 'https://login.microsoftonline.com'
login_code_url = '/common/oauth2/v2.0/authorize'
login_token_url = '/common/oauth2/v2.0/token'

list_dir_url = '/me/drive/root:/{path}:/children'
file_url = '/me/drive/root:/{path}'
upload_url = '/me/drive/root:/{path}:/content'

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


def delete_file(token, path):
    """
    :return: 204 if post successfully
    """
    url = graph_url + file_url.format(path=path)
    auth_headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
    }
    response = requests.delete(url, headers=auth_headers)
    return response.status_code


def upload_file(token, upload_path, file_path):
    # small file, upload all at once
    url = graph_url + upload_url.format(path=upload_path)
    auth_headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
    }
    response = requests.put(url, headers=auth_headers, data=open(file_path, 'rb'))
    return response


def get_context(drive, relative_path, absolute_path):
    # judge folder or file
    item = get_file(token=drive.access_token, path=absolute_path)
    if item.get('file'):
        return redirect(item.get('@microsoft.graph.downloadUrl'))

    results = list_files(token=drive.access_token, path=absolute_path).get('value')
    files = [od_path_attr(i, drive.slug, relative_path) for i in results if i.get('file')]
    dirs = [od_path_attr(j, drive.slug, relative_path) for j in results if j.get('folder')]
    readme = None
    for file in files:
        if file.get('name').lower() == 'readme.md':
            readme = get_readme(file.get('download_url'))
    context = {
        'breadcrumbs': generate_breadcrumbs(drive.slug, relative_path),
        'dirs': dirs,
        'files': files,
        'readme': readme,
        'drive_slug': drive.slug
    }
    return context


def get_password(token, path):
    res = get_file(token, path+'/private')
    download_url = res.get('@microsoft.graph.downloadUrl')
    if download_url:
        return requests.get(download_url).text
