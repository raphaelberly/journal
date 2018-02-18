# -*- coding: utf-8 -*-

import requests
from lib.base import Base
from bs4 import BeautifulSoup


class Movie(Base):

    def __init__(self, id, config_folder='config'):
        # Instantiate base
        Base.__init__(self, 'movie', config_folder)
        # Store the link parameter
        self.id = id
        self.link = self.config.get('url_title').format(self.id)
        self.soup = BeautifulSoup(requests.get(self.link).content, "html.parser") \
            .find(**self._format_params(self.config.get('content')))
        # Get the movie details
        for item in self.config['find']:
            self.__setattr__(item, self.get_from_soup(self.soup, item))

    def to_dict(self):
        keys = list(self.config['find'].keys()) + self.config['to_dict']
        output = {}
        for key in keys:
            output[key] = self.get(key)
        return output


if __name__ == '__main__':

    test = Movie('tt0449975')

    print(test.get('title'))
    print(test.get('year'))
    print(test.get('director'))
    print(test.get('actors'))
    print(test.get('poster'))

