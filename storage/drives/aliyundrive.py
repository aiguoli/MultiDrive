import requests
import json


base_url = 'https://api.aliyundrive.com/v2'
list_dir_url = '/file/list'
user_url = '/user/get'
file_download_url = '/file/get_download_url'
file_upload_url = '/file/create_with_proof'


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


def list_files(token, drive_id, path='root'):
    url = base_url + list_dir_url
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
    }
    data = {
        'drive_id': drive_id,
        'parent_file_id': path
    }
    data = json.dumps(data)
    response = requests.post(url, headers=headers, data=data).json()
    return response.get('items')


def get_download_url(token, drive_id, file_id):
    """
    :return: url, expiration(15min), size
    """
    url = base_url + file_download_url
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
    }
    data = {
        'drive_id': drive_id,
        'file_id': file_id
    }
    data = json.dumps(data)
    response = requests.post(url, headers=headers, data=data).json()
    return response
