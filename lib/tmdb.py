import json
import os
import re
from functools import lru_cache
from typing import List
from urllib.parse import urlencode

import requests
from request_boost import boosted_requests

from lib.tools import read_config


class Tmdb(object):

    URL_SEARCH = 'https://api.themoviedb.org/3/search/movie'
    URL_MOVIE = 'https://api.themoviedb.org/3/movie/{title_id}'

    def __init__(self, config_path: str = 'config'):
        credentials = read_config(os.path.join(config_path, 'credentials.yaml'))
        self._api_key = credentials['tmdb']['api_key']

    @lru_cache(24)
    def search(self, query: str) -> List[int]:
        query = re.sub('[‘’′´`˙]+', "'", query)
        params = {'query': query, 'api_key': self._api_key}
        response = requests.get(self.URL_SEARCH, params)
        return [item['id'] for item in json.loads(response.content)['results']]

    @lru_cache(96)
    def get(self, title_id: int) -> dict:
        url = self.URL_MOVIE.format(title_id=title_id)
        params = {'api_key': self._api_key, 'append_to_response': 'credits'}
        response = requests.get(url, params)
        return json.loads(response.content)

    def get_bulk(self, title_ids: List[int]) -> List[dict]:
        params = {'api_key': self._api_key, 'append_to_response': 'credits'}
        url_template = '?'.join([self.URL_MOVIE, urlencode(params)])
        urls = [url_template.format(title_id=title_id) for title_id in title_ids]
        results = boosted_requests(urls=urls)
        return results
