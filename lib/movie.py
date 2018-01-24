# -*- coding: utf-8 -*-

import re
import requests
from bs4 import BeautifulSoup
from lib.base import Base


class Movie(Base):

    def __init__(self, link, config_folder='config'):
        # Instantiate base
        Base.__init__(self, 'movie', config_folder)
        # Store the link parameter
        self.link = link
        # Compute the movie ID
        self.id = re.search(r'/(t{2}\d{7})/', link).group(1)
        # Get the movie details
        self.title = self.get_detail(link, 'title')
        self.year = self.get_detail(link, 'year')
        self.poster = self.get_detail(link, 'poster')
        self.director = self.get_detail(link, 'director')
