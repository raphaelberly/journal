import json
import os
import re
from datetime import datetime
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


class TmdbConverter(object):

    @staticmethod
    def json_to_table(item: dict) -> dict:
        output = {
            'id': item['id'],
            'imdb_id': item['imdb_id'],
            'title': item['title'],
            'release_date': datetime.strptime(item['release_date'], '%Y-%m-%d'),
            'original_title': item['original_title'],
            'original_language': item['original_language'],
            'directors': [item['name'] for item in item['credits'].get('crew', []) if item['job'] == 'Director'],
            'genres': [genre['name'] for genre in item.get('genres', [])],
            'top_cast': [item['name'] for item in item['credits'].get('cast', [])[:3]],
            'poster_path': item.get('poster_path'),
            'runtime': item.get('runtime'),
            'revenue': item.get('revenue'),
            'budget': item.get('budget'),
            'tagline': item.get('tagline'),
        }
        return output

    @staticmethod
    def table_to_front(item: dict, language: str = 'fr') -> dict:
        output = {
            'id': item['id'],
            'title': item['original_title'] if item['original_language'] == language else item['title'],
            'year': item['release_date'].year,
            'genres': item['genres'][:3],
            'cast': item['top_cast'],
            'directors': item['directors'],
            'duration': f'{item["runtime"] // 60}h {item["runtime"] % 60}min' if item.get('runtime') else None,
            'poster_url': 'https://image.tmdb.org/t/p/w200' + item['poster_path'] if item.get('poster_path') else None,
        }
        return output

    @staticmethod
    def json_to_front(item: dict, language: str = 'fr') -> dict:
        output = {
            'id': item['id'],
            'imdb_id': item['imdb_id'],
            'title': item['original_title'] if item['original_language'] == language else item['title'],
            'year': item['release_date'][:4],
            'genres': [genre['name'] for genre in item.get('genres', [])[:3]],
            'cast': [item['name'] for item in item['credits'].get('cast', [])[:4]],
            'directors': [item['name'] for item in item['credits'].get('crew', []) if item['job'] == 'Director'],
            'duration': f'{item["runtime"] // 60}h {item["runtime"] % 60}min' if item.get('runtime') else None,
            'poster_url': 'https://image.tmdb.org/t/p/w200' + item['poster_path'] if item.get('poster_path') else None,
        }
        return output
