# -*- coding: utf-8 -*-

import requests
from .base import Base
from bs4 import BeautifulSoup, SoupStrainer


class Movie(Base):

    def __init__(self, id, config_folder='config'):
        # Instantiate base
        Base.__init__(self, 'movie', config_folder)
        # Store the link parameter
        self.id = id
        self.link = self.config.get('url_title').format(self.id)
        strainer = SoupStrainer(**self._format_params(self.config.get('content')))
        self.soup = BeautifulSoup(requests.get(self.link).content, "lxml", parse_only=strainer)
        # Get the movie details
        for item in self.config['find']:
            self.__setattr__(item, self.get_from_soup(self.soup, item))

    def to_dict(self):
        keys = list(self.config['find'].keys()) + self.config['to_dict']
        output = {}
        for key in keys:
            output[key] = self.get(key)
        return output
