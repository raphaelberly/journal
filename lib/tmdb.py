import json
import os
import re
from functools import lru_cache
from multiprocessing.pool import ThreadPool

import requests

from lib.tools import read_config


class Tmdb(object):

    URL_SEARCH = 'https://api.themoviedb.org/3/search/movie'
    URL_MOVIE = 'https://api.themoviedb.org/3/movie/{movie_id}'
    URL_IMAGE = 'https://image.tmdb.org/t/p/w{width}{poster_path}'

    def __init__(self, language='fr', config_path='config'):
        credentials = read_config(os.path.join(config_path, 'credentials.yaml'))
        self.language = language
        self._api_key = credentials['tmdb']['api_key']

    @lru_cache(24)
    def search(self, query):
        query = re.sub('[‘’′´`˙]+', "'", query)
        params = {'query': query, 'api_key': self._api_key}
        response = requests.get(self.URL_SEARCH, params)
        return self._parse_search_response(response)

    @staticmethod
    def _parse_search_response(response):
        if response.status_code != 200:
            return []
        return [item['id'] for item in json.loads(response.content)['results']]

    @lru_cache(96)
    def movie(self, movie_id):
        url = self.URL_MOVIE.format(movie_id=movie_id)
        params = {'api_key': self._api_key, 'append_to_response': 'credits'}
        response = requests.get(url, params)
        return self._parse_movie_response(response)

    def _parse_movie_response(self, response):
        result = json.loads(response.content)
        # If no IMDb ID, return None
        if not (result.get('imdb_id') and result.get('title') and result.get('release_date')):
            return
        # Otherwise, compute the output dict
        output = {
            'movie': result['imdb_id'],
            'tmdb_id': result['id'],
            'title': result['original_title'] if result['original_language'] == self.language else result['title'],
            'year': result['release_date'][:4],
            'genres': [genre['name'] for genre in result.get('genres', [])[:3]],
            'cast': [item['name'] for item in result['credits'].get('cast', [])[:4]],
            'directors': [item['name'] for item in result['credits'].get('crew', []) if item['job'] == 'Director'],
            'duration': f'{result["runtime"] // 60}h {result["runtime"] % 60}min' if result.get('runtime') else None,
            'image': self.URL_IMAGE.format(width='200', poster_path=result['poster_path']) if result.get('poster_path')
                else None,
        }
        return output

    def movies(self, movie_ids):
        pool = ThreadPool(processes=len(movie_ids))
        async_results = (pool.apply_async(self.movie, (movie_id,)) for movie_id in movie_ids)
        return [async_result.get() for async_result in async_results if async_result.get()]
