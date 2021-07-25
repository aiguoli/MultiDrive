import json

import requests
from pathlib import PurePath, Path


rpc_data = {
    'jsonrpc': '2.0',
    'id': 'MultiDrive',
}

json_headers = {
    'Content-Type': 'application/json'
}


def download_with_requests(url, path, filename):
    path = Path(path)
    if path.exists():
        response = requests.get(url, stream=True).iter_content(chunk_size=1024)
        with open(path / filename, 'wb') as f:
            for i in response:
                f.write(i)
    return 'no such directory'


def aria2_rpc_add_uri(rpc_url, uris):
    """
    :param uris: a list of uri
    :return:
    """
    data = {
        'jsonrpc': '2.0',
        'id': 'MultiDrive',
        'method': 'aria2.addUri',
        'params': [
            'token:k02gmarj',
            uris
        ],
    }
    response = requests.post(rpc_url, data=json.dumps(data), headers=json_headers)
    return response


def aria2_rpc_list(rpc_url):
    data = {
        'jsonrpc': '2.0',
        'method': 'aria2.tellActive',
        'id': 1,
        'params': [
            'token:k02gmarj',
        ]
    }
    response = requests.post(rpc_url, data=json.dumps(data), headers=json_headers)
    return response


aria2_rpc_list('http://82.156.26.172:6800/jsonrpc')
