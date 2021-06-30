import json
import time

import requests
from django.shortcuts import redirect, get_object_or_404
from storage.models import File

from storage.utils import get_readme, od_path_attr, generate_breadcrumbs, utc2local

graph_url = 'https://graph.microsoft.com/v1.0'

login_base_url = 'https://login.microsoftonline.com'
login_code_url = '/common/oauth2/v2.0/authorize'
login_token_url = '/common/oauth2/v2.0/token'

list_dir_url = '/me/drive/root:/{path}:/children'
file_url = '/me/drive/root:/{path}'
upload_url = '/me/drive/root:/{path}:/content'
convert_url = '/me/drive/root:/{path}:/content?format=pdf'

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
    return response.get('value')


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


def create_folder(token, folder_name, path):
    url = graph_url + list_dir_url.format(path=path)
    auth_headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
    }
    data = {
        'name': folder_name,
        'folder': {},
        '@microsoft.graph.conflictBehavior': 'fail'
    }
    response = requests.post(url, headers=auth_headers, data=json.dumps(data)).json()
    return response


def convert_file(token, path):
    # csv、doc、docx、odp、ods、odt、pot、potm、potx、pps、ppsx、ppsxm、ppt、pptm、pptx、rtf、xls、xlsx
    # convert documents end with prefix listed above to PDF
    # if convert successfully, it will return a download url
    url = graph_url + convert_url.format(path=path)
    auth_headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
    }
    response = requests.get(url, headers=auth_headers)
    return response.url


def upload_file(token, upload_path, file_path):
    # small file, upload all at once
    url = graph_url + upload_url.format(path=upload_path)
    auth_headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
    }
    response = requests.put(url, headers=auth_headers, data=open(file_path, 'rb'))
    return response


def save_files_to_db(files, drive_id):
    # save onedrive files to database
    # sync for now because django doesn't support this very well
    if files:
        parent_file_information = files[0].get('parentReference')
        parent_file_id = parent_file_information.get('id')
        parent_path = parent_file_information.get('path').split(':')[-1]
        if parent_path == '':
            parent_path = '/'
        parent = File.objects.filter(file_id=parent_file_id).first()
        parent_id = None
        if parent:
            parent_id = parent.id
        new_files = bulk_create_files(files, parent_path, drive_id, parent_id)
        return new_files


def bulk_create_files(files, parent_path, drive_id, parent_id=None):
    bulk_files = []
    for file in files:
        bulk_files.append(File(
            name=file.get('name'),
            file_id=file.get('id'),
            size=file.get('size'),
            created=utc2local(file.get('createdDateTime')),
            updated=utc2local(file.get('lastModifiedDateTime')),
            is_dir=True if file.get('folder') else False,
            parent_path=parent_path,
            parent_id=parent_id,
            drive_id=drive_id
        ))
    File.objects.bulk_create(bulk_files)
    return bulk_files


