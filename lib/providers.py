import os

from justwatch import JustWatch

from lib.tools import read_config


class Providers(object):

    def __init__(self, config_path='config'):
        self._config = read_config(os.path.join(config_path, 'providers.yaml'))
        self._client = JustWatch(country='FR')
        self._providers_id = self._get_providers_id(self._config['supported_providers'])

    def _get_providers_id(self, supported_providers):
        providers_dict = self._client.get_providers()
        output = {}
        for item in providers_dict:
            if item['technical_name'] in supported_providers:
                output.update({item['id']: item['technical_name']})
        return output

    def get_names(self, movie_title, movie_imdb_id):
        names = set()
        results = self._client.search_title_id(movie_title)
        for _, result_id in results.items():
            result = self._client.get_title(result_id, content_type='movie')
            if {'provider': 'imdb', 'external_id': movie_imdb_id} in result['external_ids']:
                for offer in result.get('offers', []):
                    if offer['provider_id'] in self._providers_id.keys():
                        names.add(self._providers_id[offer['provider_id']])
                break
        return list(names)
