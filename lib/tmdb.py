import json
import os
import re
from functools import lru_cache
from multiprocessing.pool import ThreadPool
from typing import List

import requests

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
        if len(title_ids) == 0:
            return []
        pool = ThreadPool(processes=len(title_ids))
        async_results = (pool.apply_async(self.get, (title_id,)) for title_id in title_ids)
        return [async_result.get() for async_result in async_results if async_result.get()]
