import json
import os
import shutil
import urllib.request
import zipfile

import requests

from cachecontrol import CacheControl
from cachecontrol.caches.file_cache import FileCache

from shared import configuration
from shared.pd_exception import OperationalException

SESSION = CacheControl(requests.Session(),
                       cache=FileCache(configuration.get('web_cache')))

def unzip(url, path):
    location = '{scratch_dir}/zip'.format(scratch_dir=configuration.get('scratch_dir'))
    shutil.rmtree(location, True)
    os.mkdir(location)
    store(url, '{location}/zip.zip'.format(location=location))
    f = zipfile.ZipFile('{location}/zip.zip'.format(location=location), 'r')
    f.extractall('{location}/unzip'.format(location=location))
    f.close()
    s = open('{location}/unzip/{path}'.format(location=location, path=path), encoding='utf-8').read()
    shutil.rmtree(location)
    return s

def fetch(url, character_encoding=None, force=False):
    headers = {}
    if force:
        headers['Cache-Control'] = 'no-cache'
    print('Fetching {url} ({cache})'.format(url=url, cache='no cache' if force else 'cache ok'))
    try:
        response = SESSION.get(url, headers=headers)
        if character_encoding is not None:
            response.encoding = character_encoding
        return response.text
    except (urllib.error.HTTPError, requests.exceptions.ConnectionError) as e:
        raise FetchException(e)

def fetch_json(url, character_encoding=None):
    try:
        blob = fetch(url, character_encoding)
        return json.loads(blob)
    except json.decoder.JSONDecodeError:
        print('Failed to load JSON:\n{0}'.format(blob))
        raise

def post(url, data):
    print('POSTing to {url} with {data}'.format(url=url, data=data))
    try:
        response = SESSION.post(url, data=data)
        return response.text
    except requests.exceptions.ConnectionError as e:
        raise FetchException(e)

def store(url, path):
    print('Storing {url} in {path}'.format(url=url, path=path))
    try:
        response = requests.get(url, stream=True)
        with open(path, 'wb') as fout:
            for chunk in response.iter_content(1024):
                fout.write(chunk)
        return response
    except urllib.error.HTTPError as e:
        raise FetchException(e)

class FetchException(OperationalException):
    pass

def acceptable_file(filepath: str) -> bool:
    return os.path.isfile(filepath) and os.path.getsize(filepath) > 1000

def escape(str_input) -> str:
    # Expand 'AE' into two characters. This matches the legal list and
    # WotC's naming scheme in Kaladesh, and is compatible with the
    # image server and scryfall.
    return '+'.join(urllib.parse.quote(cardname.replace(u'Æ', 'AE')) for cardname in str_input.split(' ')).lower()
