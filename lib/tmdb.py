import json
import os
import requests
from functools import lru_cache

from lib.tools import read_config


class Tmdb(object):

    def __init__(self, config_path='config'):
        credentials = read_config(os.path.join(config_path, 'credentials.yaml'))
        self._api_key = credentials['tmdb']['api_key']
        self._conf = read_config(os.path.join(config_path, 'tmdb.yaml'))

    @lru_cache(10)
    def search(self, query):
        url = self._conf['url']['api_root'] + self._conf['url']['search']
        params = {'query': query, 'api_key': self._api_key}
        response = requests.get(url, params)
        return self._parse_search_response(response)

    @staticmethod
    def _parse_search_response(response):
        if response.status_code != 200:
            return []
        return [item['id'] for item in json.loads(response.content)['results']]

    @lru_cache(20)
    def movie(self, movie_id):
        url = self._conf['url']['api_root'] + self._conf['url']['movie'].format(movie_id=movie_id)
        params = {'api_key': self._api_key, 'append_to_response': 'credits'}
        response = requests.get(url, params)
        return self._parse_movie_response(response)

    def _parse_movie_response(self, response):
        result = json.loads(response.content)
        output = {
            'movie': result['imdb_id'],
            'tmdb_id': result['id'],
            'title': result['title'],
            'year': result['release_date'][:4],
            'duration': f'{result["runtime"] // 60}h {result["runtime"] % 60}min',
            'image': self._conf['url']['img_root'].format(width='200') + result['poster_path'],
            'genres': [genre['name'] for genre in result['genres'][:3]],
            'cast': [item['name'] for item in result['credits']['cast'][:4]],
            'directors': [
                item['name'] for item in result['credits']['crew'] if item['job'] == 'Director'
            ]
        }
        return output

    def search_movies(self, query, number_of_results):
        return [self.movie(movie_id) for movie_id in self.search(query)[:number_of_results]]
