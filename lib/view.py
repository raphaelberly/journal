# -*- coding: utf-8 -*-

import re
import string
import requests
from lib.base import Base
from bs4 import BeautifulSoup


class View(Base):

    def __init__(self, input, config_folder='config'):
        # Instantiate base
        Base.__init__(self, 'view', config_folder)
        # Get attributes
        self.input = self._clean_string(input)
        self.link = self._get_link()
        self.soup = BeautifulSoup(requests.get(self.link).content, "html.parser") \
            .find(**self._format_params(self.config.get('content')))
        self.ids = self._get_ids()

    @staticmethod
    def _clean_string(input):
        punctuation = re.compile("[{}]".format(re.escape(string.punctuation)))
        aux = punctuation.sub('', input)
        aux = re.sub("\s\s+", " ", aux)
        return aux.lower().strip(' ')

    def _get_link(self):
        return self.config.get('url_search').format("+".join(self.input.split(" ")))

    def _get_ids(self):
        result = self.get_from_soup(self.soup, 'first_results')
        pattern = re.compile(r'/(t{2}\d{7})/')
        return [pattern.search(item).group(1) for item in result]


if __name__ == '__main__':

    test = View("sing !", 'config')

    from lib.movie import Movie
    for id in test.ids[:3]:
        movie = Movie(id)
        print('{0} ({1}), id "{2}", by {3}, with {4}'.format(
            movie.get('title'), movie.get('year'), movie.get('id'), ' and '.join(movie.get('director')), ', '.join(movie.get('actors'))))
