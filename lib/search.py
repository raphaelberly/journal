import re
import string

import requests
from bs4 import BeautifulSoup, SoupStrainer

from .base import Base


class Search(Base):

    def __init__(self, raw_input, config_folder='config'):
        # Instantiate base
        Base.__init__(self, 'search', config_folder)
        # Parse data
        input = self._clean_string(raw_input)
        self.link = self._get_link(input)

    def _get_link(self, input):
        url = self.config['url']
        return url['root'].format(
            search_string="+".join(input.split(" ")),
            types_string=','.join(url['types']),
            min_votes=url['min_votes']
        )

    def get_results(self):

        strainer = SoupStrainer(**self._format_params(self.config.get('content')))
        headers = {"Accept-Language": "en-US,en;q=0.5"}
        soup = BeautifulSoup(requests.get(self.link, headers=headers).content, 'lxml', parse_only=strainer)

        rows = self.get_from_soup(soup, 'rows')
        if not rows:
            return []

        rows = rows[:self.config['nb_results']]

        id_pattern = re.compile(r'/(t{2}\d{7})/')
        year_pattern = re.compile(r'\((\d{4})\)')
        directors_pattern = re.compile(r'li_dr_\d')
        cast_pattern = re.compile(r'li_st_\d')

        output = []

        for row in rows:

            sub_output = {}
            sub_output.update({'id': self._regexp_extract(id_pattern, self.get_from_soup(row, 'id'))})
            sub_output.update({'title': self.get_from_soup(row, 'title')})
            sub_output.update({'genre': self.get_from_soup(row, 'genre')})
            sub_output.update({'year': self._regexp_extract(year_pattern, self.get_from_soup(row, 'year'))})

            staff = self.get_from_soup(row, 'staff')
            sub_output.update({'directors': [item.text for item in staff.find_all('a', href=directors_pattern)]})
            sub_output.update({'cast': [item.text for item in staff.find_all('a', href=cast_pattern)]})

            img = self.get_from_soup(row, 'image')
            sub_output.update({'image': self._magnify_image(img)})

            output.append(sub_output)

        return output

    @staticmethod
    def _clean_string(input):
        punctuation = re.compile("[{}]".format(re.escape(string.punctuation)))
        aux = punctuation.sub('', input)
        aux = re.sub("\s\s+", " ", aux)
        return aux.lower().strip(' ')

    @staticmethod
    def _regexp_extract(pattern, string):
        result = pattern.search(string)
        if result:
            return pattern.search(string).group(1)
        else:
            return None

    def _magnify_image(self, image):
        output = image
        for change in self.config['images']:
            output = output.replace(change['smaller'], change['bigger'])
        return output
