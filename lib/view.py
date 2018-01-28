# -*- coding: utf-8 -*-

import re
import string
import requests
from bs4 import BeautifulSoup
from lib.base import Base


class View(Base):

    def __init__(self, input, config_folder='config'):
        # Instantiate base
        Base.__init__(self, 'view', config_folder)
        # Get attributes
        self.input = self._clean_string(input)
        self.ids = self._get_ids()

    @staticmethod
    def _clean_string(input):
        punctuation = re.compile("[{}]".format(re.escape(string.punctuation)))
        aux = punctuation.sub('', input)
        aux = re.sub("\s\s+", " ", aux)
        return aux.lower().strip(' ')

    def _get_movie_id(self):
        # Get the page link
        link = self.config.get('url_search').format("+".join(self.input.split(" ")))
        result = self.get_detail(link, 'first_results')
        return re.search(r"/(t{2}\d{7})/", result).group(1)

    def _get_ids(self):
        link = self.config.get('url_search').format("+".join(self.input.split(" ")))
        print(link)
        result = self.get_detail(link, 'first_results')
        pattern = re.compile(r'/(t{2}\d{7})/')
        return [pattern.search(item).group(1) for item in result]
