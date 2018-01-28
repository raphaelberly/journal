# -*- coding: utf-8 -*-

import re
import requests
from bs4 import BeautifulSoup
from lib.base import Base


class Movie(Base):

    def __init__(self, id, config_folder='config'):
        # Instantiate base
        Base.__init__(self, 'movie', config_folder)
        # Store the link parameter
        self.id = id
        self.link = self.config.get('url_title').format(self.id)
        # Get the movie details
        self.title = self.get_detail(self.link, 'title')
        self.year = self.get_detail(self.link, 'year')
        self.poster = self.get_detail(self.link, 'poster')
        self.director = self.get_detail(self.link, 'director')
