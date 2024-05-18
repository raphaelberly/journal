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
        response = self.session.post(self.BASE_URL + 'auth/local', data=json.dumps(_credentials), headers=self.HEADERS)
        self.account_id = json.loads(response.content)['id']

    @property
    def request_statuses(self) -> dict:
        query = f'request?take={self.DEFAULT_REQUEST_NB}&requestedBy={self.account_id}&skip=0&sort=added'
        response = self.session.get(self.BASE_URL + query)
        results = json.loads(response.content)['results']
        return {item['media']['tmdbId']: item['status'] for item in results}

    def request_title(self, tmdb_id: int) -> None:
        payload = {'mediaId': tmdb_id, 'mediaType': 'movie', 'is4k': False}
        self.session.post(self.BASE_URL + 'request', data=json.dumps(payload), headers=self.HEADERS)
