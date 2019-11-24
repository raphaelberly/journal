import os

from justwatch import JustWatch

from lib.tools import read_config


class Providers(object):

    PRECISION = 5

    def __init__(self, config_path='config'):
        self._config = read_config(os.path.join(config_path, 'providers.yaml'))
        self._client = JustWatch(country='FR')
        self.supported_providers = self._get_providers_id(self._config['supported_providers'])

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
        results = self._client.search_for_item(query=movie_title, providers=list(self.supported_providers.values()),
                                               content_types=['movie'], page_size=self.PRECISION)['items']
        for result in results:
            if self._check_tmdb_id(result['scoring'], movie_tmdb_id):
                for offer in result.get('offers', []):
                    if offer['provider_id'] in self.supported_providers.keys():
                        names.add(self.supported_providers[offer['provider_id']])
                break
        return list(names)
