import requests

from storage.models import File
from storage.utils import timestamp2datetime

base_auth_url = 'http://openapi.baidu.com'
authorize_url = '/oauth/2.0/authorize'
access_token_url = '/oauth/2.0/token'

base_url = 'https://pan.baidu.com'
file_url = '/rest/2.0/xpan/file'
specific_file_url = '/rest/2.0/xpan/multimedia'


def get_authorization_code(client_id, redirect_uri):
    url = base_auth_url + authorize_url
    params = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': 'basic,netdisk',
        'display': 'tv',
        'qrcode': 1,
        'force_login': 1
    }
    response = requests.get(url, params=params)
    return response.url


def get_access_token(code, client_id, client_secret, redirect_uri):
    # expired in 30 days
    url = base_auth_url + access_token_url
    params = {
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
    }
    response = requests.get(url, params=params).json()
    return response


def get_refresh_token(refresh_token, client_id, client_secret):
    url = base_auth_url + access_token_url
    params = {
        'grant_type': 'get_refresh_token',
        'get_refresh_token': refresh_token,
        'client_id': client_id,
        'client_secret': client_secret
    }
    response = requests.get(url, params=params).json()
    return response


def list_files(access_token, path='/', order='name', desc=None, start=0, limit=1000, folder=0):
    url = base_url + file_url
    params = {
        'method': 'list',
        'access_token': access_token,
        'dir': path,
        'order': order,
        'desc': desc,
        'start': start,
        'limit': limit,
        'folder': folder
    }
    response = requests.get(url, params=params).json()
    return response.get('list')


def list_specific_files(access_token, category, path, ext=None, order='name', desc=None, start=0, limit=1000):
    # category: 1 video、2 audio、3 pic、4 doc、5 app、6 other、7 bt  split with ','
    # ext: extension of files, the default value is all ext in the category. split with ','
    url = base_url + specific_file_url
    params = {
        'method': 'categorylist',
        'access_token': access_token,
        'category': category,
        'parent_path': path,
        'order': order,
        'desc': desc,
        'start': start,
        'limit': limit,
    }
    response = requests.get(url, params=params).json()
    return response.get('list')


def search_files(access_token, key, path, recursion=0, page=None, num=1000, web=0):
    url = base_url + file_url
    params = {
        'method': 'search',
        'access_token': access_token,
        'key': key,
        'dir': path,
        'recursion': recursion,
        'page': page,
        'num': num,
        'web': web
    }
    response = requests.get(url, params=params).json()
    return response.get('list')


def get_file(access_token, fsids, path=None, thumb=0, dlink=1, extra=0):
    # it's wired that download is not stable...
    url = base_url + specific_file_url
    headers = {
        'User-Agent': 'pan.baidu.com',
    }
    params = {
        'method': 'filemetas',
        'access_token': access_token,
        'fsids': str(fsids),
        'path': path,
        'thumb': thumb,
        'dlink': dlink,
        'extra': extra
    }
    response = requests.get(url, params=params, headers=headers).json()
    return response.get('list')


def save_files_to_db(files, drive_id, parent_path, parent_id=None):
    if files:
        # api of baidu disk is designed by devil
        new_files = []
        for file in files:
            new_files.append(File(
                name=file.get('server_filename'),
                file_id=file.get('fs_id'),
                parent_path=parent_path,
                is_dir=True if file.get('isdir') == 0 else False,
                size=file.get('size'),
                drive_id=drive_id,
                parent_id=parent_id,
                created=timestamp2datetime(file.get('local_ctime')),
                updated=timestamp2datetime(file.get('local_mtime')),
            ))
        File.objects.bulk_create(new_files)

