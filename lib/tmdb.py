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
    URL_PROVIDERS = 'https://api.themoviedb.org/3/movie/{title_id}/watch/providers'

    def __init__(self, config_path: str = 'config'):
        credentials = read_config(os.path.join(config_path, 'credentials.yaml'))
        self._api_key = credentials['tmdb']['api_key']
        providers_config = read_config(os.path.join(config_path, 'providers.yaml'))
        self._country = providers_config['country']
        self._supported_providers = providers_config['supported_providers']

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
        response = json.loads(requests.get(url, params).content)
        if response.get('success', True) is False:
            raise RuntimeError(f'Could not find title: {title_id}')
        return response

    def get_bulk(self, title_ids: List[int]) -> List[dict]:
        params = {'api_key': self._api_key, 'append_to_response': 'credits'}
        url_template = '?'.join([self.URL_MOVIE, urlencode(params)])
        urls = [url_template.format(title_id=title_id) for title_id in title_ids]
        results = boosted_requests(urls=urls)
        return [result for result in results if result is not None]

    @staticmethod
    def _clean_name(name):
        return name.lower().replace(" ", "").replace("+", "")

    def providers(self, title_id: int) -> List[str]:
        url = self.URL_PROVIDERS.format(title_id=title_id)
        params = {'api_key': self._api_key}
        response = json.loads(requests.get(url, params).content)
        if response.get('success', True) is False:
            raise RuntimeError(f'Could not find providers for title: {title_id}')
        results = [
            self._clean_name(item['provider_name'])
            for item in response['results'].get('FR', {}).get('flatrate', [])
            if self._clean_name(item['provider_name']) in self._supported_providers
        ]
        return results
