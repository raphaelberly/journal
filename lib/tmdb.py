import json
import os
import re
from functools import lru_cache

import requests

from lib.langdetect import detect
from lib.tools import read_config


class Tmdb(object):

    def __init__(self, config_path='config'):
        credentials = read_config(os.path.join(config_path, 'credentials.yaml'))
        self._api_key = credentials['tmdb']['api_key']
        self._conf = read_config(os.path.join(config_path, 'tmdb.yaml'))

    @lru_cache(8)
    def search(self, query):
        query = re.sub('[‘’′´`˙]+', "'", query)
        url = self._conf['url']['api_root'] + self._conf['url']['search']
        params = {'query': query, 'api_key': self._api_key}
        response = requests.get(url, params)
        return self._parse_search_response(response)

    @staticmethod
    def _parse_search_response(response):
        if response.status_code != 200:
            return []
        return [item['id'] for item in json.loads(response.content)['results']]

    @lru_cache(24)
    def movie(self, movie_id):
        url = self._conf['url']['api_root'] + self._conf['url']['movie'].format(movie_id=movie_id)
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
            'title': result['original_title'] if detect(result['original_title']) == 'fr' else result['title'],
            'year': result['release_date'][:4],
            'genres': [genre['name'] for genre in result.get('genres', [])[:3]],
            'cast': [item['name'] for item in result['credits'].get('cast', [])[:4]],
            'directors': [item['name'] for item in result['credits'].get('crew', [])
                          if item['job'] == 'Director'],
            'duration': f'{result["runtime"] // 60}h {result["runtime"] % 60}min' if
                        result.get('runtime') else None,
            'image': None if not result.get('poster_path') else
                    self._conf['url']['img_root'].format(width='200') + result['poster_path'],
        }
        return output

    def search_movies(self, query, number_of_results):
        i = 0
        output = []
        results = self.search(query)
        while (len(output) < number_of_results) and (i < len(results)):
            result = self.movie(results[i])
            if result:
                output.append(result)
            i += 1
        return output, i < len(results)
