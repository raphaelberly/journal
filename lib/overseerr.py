import json
import os

import requests

from lib.tools import read_config


class Overseerr(object):

    BASE_URL = 'https://request.teulon.eu:443/api/v1/'
    HEADERS = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }
    DEFAULT_REQUEST_NB = 200

    def __init__(self, config_path: str = 'config'):
        _credentials = read_config(os.path.join(config_path, 'credentials.yaml'))['overseerr']
        self.session = requests.Session()
        url = self.BASE_URL + 'auth/local'
        try:
            response = self.session.post(url, data=json.dumps(_credentials), headers=self.HEADERS)
            # If no ConnectionError was raised but status >= 300, raise it
            if response.status_code >= 300:
                raise requests.exceptions.ConnectionError
        except requests.exceptions.ConnectionError:
            self.is_available = False
            self.account_id = None
        else:
            self.is_available = True
            self.account_id = json.loads(response.content)['id']

    def request_status(self, tmdb_id: int) -> int:
        response = self.session.get(self.BASE_URL + f'movie/{tmdb_id}')
        try:
            return json.loads(response.content)['mediaInfo']['status']
        except KeyError:
            return -1

    @property
    def request_statuses(self) -> dict:
        query = f'request?take={self.DEFAULT_REQUEST_NB}&requestedBy={self.account_id}&skip=0&sort=added'
        response = self.session.get(self.BASE_URL + query)
        results = json.loads(response.content)['results']
        output = {}
        for item in results:
            if item['status'] < 2:
                output[item['media']['tmdbId']] = item['status']
            else:
                output[item['media']['tmdbId']] = item['media']['status']
        return output

    def request_title(self, tmdb_id: int) -> None:
        payload = {'mediaId': tmdb_id, 'mediaType': 'movie', 'is4k': False}
        self.session.post(self.BASE_URL + 'request', data=json.dumps(payload), headers=self.HEADERS)
