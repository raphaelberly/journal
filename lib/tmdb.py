import json
import os
import requests

from lib.tools import read_config


class Tmdb(object):

    def __init__(self, config_path='config'):
        credentials = read_config(os.path.join(config_path, 'credentials.yaml'))
        self._api_key = credentials['tmdb']['api_key']
        self._conf = read_config(os.path.join(config_path, 'tmdb.yaml'))

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

    def movie(self, movie_id):
        url = self._conf['url']['api_root'] + self._conf['url']['movie'].format(movie_id=movie_id)
        params = {'api_key': self._api_key, 'append_to_response': 'credits'}
        response = requests.get(url, params)
        return self._parse_movie_response(response)

    def _parse_movie_response(self, response):
        if response.status_code != 200:
            return {}
        result = json.loads(response.content)
        output = {
            result['imdb_id']: {
                'movie': result['imdb_id'],
                'tmdb_id': result['id'],
                'title': result['title'],
                'year': result['release_date'][:4],
                'image': self._conf['url']['img_root'].format(width='180') + result['poster_path'],
                'genres': [genre['name'] for genre in result['genres']],
                'cast': [item['name'] for item in result['credits']['cast'][:3]],
                'directors': [
                    item['name'] for item in result['credits']['crew'] if item['job'] == 'Director'
                ]
            }
        }
        return output