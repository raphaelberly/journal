# -*- coding: utf-8 -*-

import re
import os
import string
import requests
from bs4 import BeautifulSoup
from lib.utils import read_config, read_credentials


class View:

    def __init__(self, input, config_folder):
        # Load credentials and config
        self.credentials = read_credentials(os.path.join(config_folder, 'credentials.ini'))
        self.config = read_config(os.path.join(config_folder, 'view.yaml'))
        # Get attributes
        self.input = self._clean_string(input)
        self.id = self._get_movie_id()

    @staticmethod
    def _clean_string(input):
        punctuation = re.compile("[{}]".format(re.escape(string.punctuation)))
        aux = punctuation.sub('', input)
        aux = re.sub("\s\s+", " ", aux)
        return aux.lower().strip(' ')

    def _get_find_params(self, id):
        return {'name': self.config.get('find').get(id).get('tag'),
                'attrs': {self.config.get('find').get(id).get('type'): self.config.get('find').get(id).get('key')}}

    def _get_movie_id(self):
        source = requests.get(self.config.get('url_search').format("+".join(self.input.split(" ")))).content
        # Extract the first result from the source
        first_result = BeautifulSoup(source, "html.parser").find(**self._get_find_params('first_result'))
        if first_result is None:
            raise ValueError('Could not find any result for given string')
        # Extract the ID and return it
        link = first_result.find('a')['href']
        return re.search(r'/(t{2}\d{7})/', link).group(1)
