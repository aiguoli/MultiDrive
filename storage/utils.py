import datetime
import re
from pathlib import Path, PurePath, PurePosixPath
from urllib import parse

import requests
from django.core.cache import cache
from django.urls import reverse


def utc2local(utc_str):
    # aliyundrive return a utctime string with float behind seconds while onedrive won' t
    if len(utc_str) == 20:
        utc_format = '%Y-%m-%dT%H:%M:%SZ'
    else:
        utc_format = '%Y-%m-%dT%H:%M:%S.%fZ'
    res = datetime.datetime.strptime(utc_str, utc_format) + datetime.timedelta(hours=8)
    return res.strftime('%Y-%m-%d %H:%M:%S')


def timestamp2datetime(timestamp):
    return datetime.datetime.fromtimestamp(timestamp)


def path_attr(root, drive_slug, full_path):
    path_info = full_path.stat()
    basename = full_path.name
    relative_path = full_path.relative_to(root)
    information = {
        'name': basename,
        'size': convert_size(path_info.st_size),
        'modified': convert_time(path_info.st_mtime),
        'is_dir': True if full_path.is_dir() else False,
        'id': relative_path.as_posix(),
        'url': reverse('storage:list_files', args=(drive_slug, relative_path.as_posix()))
    }
    return information


def convert_size(text):
    if text == 0:
        return 0
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    size = 1024
    for i in range(len(units)):
        if (text / size) < 1:
            return "%.2f%s" % (text, units[i])  # 返回值保留小数点后两位
        text = text / size


def convert_time(timestamp):
    time_array = datetime.datetime.fromtimestamp(timestamp)
    current_time = datetime.datetime.now()
    time_format = '%Y年%m月'
    if time_array.year == current_time.year:
        time_format = '%m月%d日'
    return time_array.strftime(time_format)


def file_type(prefix):
    file_types = {
        'text': ['txt', 'html', 'md', 'py', 'php', 'cpp'],
        'image': ['jpg', 'jpeg', 'png', 'gif', 'ico', 'jpe', 'jfif', 'tif', 'tiff', 'heic', 'webp', 'bmp'],
        'office': ['ppt', 'pptx', 'pptm', 'doc', 'docx', 'xls'],
        'video': ['mp4', 'webm', 'avi', 'mpg', 'mpeg', 'rm', 'rmvb', 'mov', 'wmv', 'mkv', 'asf'],
        'audio': ['mp3', 'wav', 'ogg']
    }
    res = None
    for i in file_types:
        if prefix.lower() in file_types[i]:
            res = i
    return res


def get_param_from_url(param_name, url):
    params = parse.parse_qs(parse.urlparse(url).query)
    return params.get(param_name)[0]


def get_aliyundrive_filename(url):
    pattern = re.compile('filename%2A%3DUTF-8%27%27(.*?)&u', re.S)
    encoded_param = pattern.findall(url)[0]
    # it' s wired, the param should be unquoted twice
    result = parse.unquote(parse.unquote(encoded_param))
    return result


def od_path_attr(item, drive_slug, path):
    name = item.get('name')
    parent_dir = item.get('parentReference').get('path').replace('/drive/root:', '')
    if parent_dir == '':
        parent_dir = '/'
    path = str(PurePath(path, name).as_posix())
    url = reverse('storage:list_files', args=(drive_slug, path))
    res = {
        'name': name,
        'size': convert_size(item.get('size')),
        'modified': utc2local(item.get('lastModifiedDateTime')),
        'url': url,
        'path': parent_dir.replace('/', '%2F')
    }
    return res


def ali_path_attr(item, drive_slug, file_id):
    name = item.get('name')
    url = reverse('storage:list_files', args=(drive_slug, file_id))
    modified = item.get('updated_at')
    res = {
        'name': name,
        'drive_slug': drive_slug,
        'modified': utc2local(modified),
        'url': url,
        'file_id': file_id,
        'download_url': item.get('download_url')
    }
    return res


def get_readme(url):
    if url:
        response = requests.get(url)
        response.encoding = 'utf-8'
        return response.text
    return None


def generate_breadcrumbs(drive_slug, path):
    path = PurePosixPath(path)
    home = {'path': 'Home', 'url': reverse('storage:list_files', args=(drive_slug,))}
    if str(path) == '/':
        return [home]

    path_slice = path.parts
    temp = ''
    res = [home]
    for i in path_slice[1:]:
        temp += '/' + i
        res.append({
            'path': i,
            'url': reverse('storage:list_files', args=(drive_slug, temp))
        })
    return res


# functions for refreshing onedrive cache
# still developing...
def assign(data, indices, value):
    """
    Modified value in a specific path in a nested dict.
    :param data: a dict
    :param indices: a list that consists of slices of path
    :param value: assignment
    :return:
    """
    if len(indices) == 1:
        data[indices[0]] = value
        return
    if data.get(indices[0]):
        next_path = data[indices[0]]
        if next_path.get('children'):
            next_path = next_path['children']
        assign(next_path, indices[1:], value)


def lookup(data, indices):
    if len(indices) == 1:
        return data[indices[0]]
    if data.get(indices[0]):
        next_path = data[indices[0]]
        if next_path.get('children'):
            next_path = next_path['children']
        return lookup(next_path, indices[1:])


def clean_data(data):
    """
    :param data: comes from onedrive.list_file.get('value')
    :return: content could be insert to children of cache
    """
    content = []
    for item in data:
        content.append({
            'name': item.get('name'),
            'type': list(item.keys())[-1],
            'modified': item.get('lastModifiedDateTime'),
            'size': item.get('size'),
            'children': []
        })
    return content


def assign_onedrive_cache(data, drive_slug, full_path):
    # data是onedrive.list_file.get('value')
    # the format of full_path is '/path/to/file'
    new_children = clean_data(data)
    if full_path == '/':
        path_list = ['root']
    else:
        path_list = full_path.split('/')[1:]
    new_cache = cache.get(drive_slug)
    assign(new_cache, path_list, new_children)
    cache.set(drive_slug, new_cache)
