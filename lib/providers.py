import os
from datetime import date
from time import sleep

from justwatch import JustWatch
from requests import HTTPError

from lib.tools import read_config


class Providers(object):

    PRECISION = 5
    DATE_FORMAT = '%Y-%m-%d'

    def __init__(self, config_path='config'):
        config = read_config(os.path.join(config_path, 'providers.yaml'))
        self.country = config['country']
        self.main_city = config['main_city']
        self._client = JustWatch(country=self.country)
        self.supported_providers = self._get_providers_id(config['supported_providers'])

    def _get_providers_id(self, supported_providers):
        providers_dict = self._client.get_providers()
        output = {}
        for item in providers_dict:
            if item['technical_name'] in supported_providers:
                output.update({item['id']: item['technical_name']})
        return output

    @staticmethod
    def _check_tmdb_id(scoring_list, movie_tmdb_id):
        for item in scoring_list:
            if item['provider_type'] == 'tmdb:id':
                if item['value'] == movie_tmdb_id:
                    return True
        return False

    def get_names(self, movie_title, movie_tmdb_id):
        names = set()
        kwargs = {
            'query': movie_title,
            'providers': list(self.supported_providers.values()),
            'content_types': ['movie'],
            'page_size': self.PRECISION,
        }
        try:
            response = self._client.search_for_item(**kwargs)
        except HTTPError:
            sleep(0.1)
            response = self._client.search_for_item(**kwargs)
        for result in response['items']:
            if self._check_tmdb_id(result['scoring'], movie_tmdb_id):
                for offer in result.get('offers', []):
                    if offer['provider_id'] in self.supported_providers.keys():
                        names.add(self.supported_providers[offer['provider_id']])
                today = date.today().strftime(self.DATE_FORMAT)
                if self._client.get_cinema_times(result['id'], date=today, **self.main_city):
                    names.add('cinema')
                break
        return list(names)
