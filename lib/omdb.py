import json
import os
from functools import lru_cache
from typing import Optional, List

import requests
from request_boost import boosted_requests

from lib.tools import read_config


class Omdb(object):

    URL_MOVIE = 'http://www.omdbapi.com/?apikey={api_key}&i={title_id}'

    def __init__(self, config_path: str = 'config'):
        credentials = read_config(os.path.join(config_path, 'credentials.yaml'))
        self._api_key = credentials['omdb']['api_key']

    @lru_cache(96)
    def _get(self, title_id: str) -> dict:
        url = self.URL_MOVIE.format(api_key=self._api_key, title_id=title_id)
        response = requests.get(url)
        if response.status_code == 200:
            response = json.loads(response.content)
            if response['Response'] == 'True':
                return response
        return {}

    def _get_bulk(self, title_ids: List[int]) -> List[dict]:
        urls = [self.URL_MOVIE.format(api_key=self._api_key, title_id=title_id) for title_id in title_ids]
        results = boosted_requests(urls=urls)
        return [result if result['Response'] == 'True' else {} for result in results]

    def imdb_rating(self, title_id: str) -> Optional[float]:
        try:
            return float(self._get(title_id).get('imdbRating'))
        except (ValueError, TypeError):
            return None

    def imdb_ratings(self, title_ids: List[int]) -> List[Optional[float]]:
        results = self._get_bulk(title_ids)
        output = []
        for result in results:
            try:
                output.append(float(result.get('imdbRating')))
            except (ValueError, TypeError):
                output.append(None)
        return output
