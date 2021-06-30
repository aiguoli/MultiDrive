import requests
import json

from django.shortcuts import redirect
from django.urls import reverse

from storage.models import File
from storage.utils import ali_path_attr, get_readme, utc2local

base_url = 'https://api.aliyundrive.com/v2'

list_dir_url = '/file/list'
user_url = '/user/get'
file_download_url = '/file/get_download_url'
file_upload_url = '/file/create_with_proof'
file_temporarily_remove_url = '/recyclebin/trash'


def refresh_token(refresh_token):
    """
    :return access_token refresh_token
    """
    # Notice that: refresh_token should be taken in web login url ('passport.aliyundrive.com/newlogin/sms/login.do')
    # by mobile verify code then do base64 decoding for the 'bizExt', the refresh_token of the result is what you need
    # otherwise, aliyundrive' s referer policy will destroy this script
    # url = 'https://websv.aliyundrive.com/token/refresh'   # web version
    url = 'https://auth.aliyundrive.com/v2/account/token'   # mobile version
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token
    }
    data = json.dumps(data)
    response = requests.post(url, data=data).json()
    return response


def get_user_info(token):
    # 'default_drive_id' comes from here
    url = base_url + user_url
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
    }
    data = '{}'
    response = requests.post(url, headers=headers, data=data).json()
    return response


def list_files(access_token, drive_id, path='root'):
    url = base_url + list_dir_url
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + access_token
    }
    data = {
        'drive_id': drive_id,
        'parent_file_id': path
    }
    response = requests.post(url, headers=headers, data=json.dumps(data)).json()
    return response.get('items')


def get_download_url(access_token, drive_id, file_id):
    """
    :return: url, expiration(15min), size
    """
    url = base_url + file_download_url
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + access_token
    }
    data = {
        'drive_id': drive_id,
        'file_id': file_id
    }
    data = json.dumps(data)
    response = requests.post(url, headers=headers, data=data).json()
    return response


def temporarily_delete_file(access_token, drive_id, file_id):
    # move file to trash bin
    url = base_url + file_temporarily_remove_url
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + access_token
    }
    data = {
        'drive_id': drive_id,
        'file_id': file_id
    }
    data = json.dumps(data)
    response = requests.post(url, headers=headers, data=data).status_code
    return response


def get_context(drive, path):
    if path == '':
        path = 'root'
    results = list_files(access_token=drive.access_token, drive_id=drive.client_id, path=path)
    if results is None:
        result = get_download_url(access_token=drive.access_token, drive_id=drive.client_id, file_id=path)
        return redirect(result.get('url'), Referer='https://www.aliyundrive.com/')
    dirs = [ali_path_attr(i, drive.slug, i.get('file_id')) for i in results if i.get('type') == 'folder']
    files = [ali_path_attr(j, drive.slug, j.get('file_id')) for j in results if j.get('type') == 'file']
    readme = None
    for file in files:
        if file.get('name').lower == 'readme.md':
            readme = get_readme(file.get('download_url'))
    context = {
        'root': reverse('storage:index'),
        'dirs': dirs,
        'files': files,
        'readme': readme,
        'drive_slug': drive.slug
    }
    return context


def save_files_to_db(files, drive_id, parent_path):
    if files:
        if parent_path == 'root':
            parent_path = '/'
        parent_file_id = files[0].get('parent_file_id')
        parent = File.objects.filter(file_id=parent_file_id).first()
        new_files = []
        for file in files:
            new_files.append(File(
                name=file.get('name'),
                file_id=file.get('file_id'),
                created=utc2local(file.get('created_at')),
                updated=utc2local(file.get('updated_at')),
                drive_id=drive_id,
                size=file.get('size'),
                is_dir=True if file.get('type') == 'folder' else False,
                parent_path=parent_path,
                parent_id=parent.id if parent else None
            ))
        File.objects.bulk_create(new_files)


