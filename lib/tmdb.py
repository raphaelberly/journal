import os
import re
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from typing import List, Optional

import requests
from requests.adapters import HTTPAdapter

from lib.tools import read_config


class Tmdb(object):

    URL_SEARCH = 'https://api.themoviedb.org/3/search/movie'
    URL_MOVIE = 'https://api.themoviedb.org/3/movie/{title_id}'
    URL_PROVIDERS = 'https://api.themoviedb.org/3/movie/{title_id}/watch/providers'
    # A search returns at most 20 titles, all fetched at once by get_bulk
    MAX_PARALLEL_REQUESTS = 20
    TIMEOUT = 10
    # Every movie genre of TMDb (GET /genre/movie/list), in alphabetical order, as stored in journal.titles
    GENRES = [
        'Action', 'Adventure', 'Animation', 'Comedy', 'Crime', 'Documentary', 'Drama', 'Family', 'Fantasy',
        'History', 'Horror', 'Music', 'Mystery', 'Romance', 'Science Fiction', 'Thriller', 'TV Movie', 'War',
        'Western',
    ]

    def __init__(self, config_path: str = 'config'):
        credentials = read_config(os.path.join(config_path, 'credentials.yaml'))
        self._api_key = credentials['tmdb']['api_key']
        providers_config = read_config(os.path.join(config_path, 'providers.yaml'))
        self._country = providers_config['country']
        self._supported_providers = providers_config['supported_providers']
        # Keep the connections alive between calls, and get gzipped responses: a new TLS connection per call
        # and uncompressed credits (~5x bigger) used to be most of the time a search takes
        self._session = requests.Session()
        self._session.headers['Accept-Encoding'] = 'gzip'
        self._session.mount('https://', HTTPAdapter(pool_maxsize=self.MAX_PARALLEL_REQUESTS, max_retries=1))
        self._executor = ThreadPoolExecutor(self.MAX_PARALLEL_REQUESTS, thread_name_prefix='tmdb')

    def _get_json(self, url: str, **params) -> dict:
        response = self._session.get(url, params={'api_key': self._api_key, **params}, timeout=self.TIMEOUT)
        return response.json()

    @lru_cache(24)
    def search(self, query: str) -> List[int]:
        query = re.sub('[‘’′´`˙]+', "'", query)
        response = self._get_json(self.URL_SEARCH, query=query)
        return [item['id'] for item in response['results']]

    def _get(self, title_id: int) -> dict:
        response = self._get_json(self.URL_MOVIE.format(title_id=title_id), append_to_response='credits')
        if response.get('success', True) is False:
            raise RuntimeError(f'Could not find title: {title_id}')
        return response

    @lru_cache(96)
    def get(self, title_id: int) -> dict:
        return self._get(title_id)

    def _get_or_none(self, title_id: int) -> Optional[dict]:
        try:
            return self._get(title_id)
        except (requests.RequestException, RuntimeError):
            return None

    def get_bulk(self, title_ids: List[int]) -> List[dict]:
        # Fetch in parallel and skip the titles that fail. Bypass the cache of get: search results would fill it
        # with dicts of up to 600 KB each, while TMDb's CDN serves a title fetched again in ~20 ms
        results = self._executor.map(self._get_or_none, title_ids)
        return [result for result in results if result is not None]

    @staticmethod
    def _clean_name(name):
        return name.lower().replace(" ", "").replace("+", "")

    def providers(self, title_id: int) -> List[str]:
        response = self._get_json(self.URL_PROVIDERS.format(title_id=title_id))
        if response.get('success', True) is False:
            raise RuntimeError(f'Could not find providers for title: {title_id}')
        results = [
            self._clean_name(item['provider_name'])
            for item in response['results'].get('FR', {}).get('flatrate', [])
            if self._clean_name(item['provider_name']) in self._supported_providers
        ]
        return results
