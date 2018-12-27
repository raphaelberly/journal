# -*- coding: utf-8 -*-
from itertools import islice as slice

import os
import re
import requests
import string
from bs4 import BeautifulSoup, SoupStrainer

from lib.tools import read_config, resolve


class Search(object):

    def __init__(self, raw_input, config_folder='config'):
        # Config
        self.config = read_config(os.path.join(config_folder, 'search.yaml'))
        self.credentials = read_config(os.path.join(config_folder, 'credentials.yaml'))
        # Parse data
        input = self._clean_string(raw_input)
        self.link = self._get_link(input)

    @staticmethod
    def _clean_string(input):
        punctuation = re.compile("[{}]".format(re.escape(string.punctuation)))
        aux = punctuation.sub('', input)
        aux = re.sub("\s\s+", " ", aux)
        return aux.lower().strip(' ')

    def _get_link(self, input):
        url = self.config['url']
        return url['root'].format(
            search_string="+".join(input.split(" ")),
            types_string=','.join(url['types']),
            min_votes=url['min_votes']
        )

    @staticmethod
    def _format_params(params):
        if 'tag' not in params:
            raise KeyError(f"'tag' key must be in {params}")
        if params.get('type') and params.get('key'):
            return {'name': params.get('tag'), 'attrs': {params.get('type'): params.get('key')}}
        else:
            return {'name': params.get('tag')}

    @staticmethod
    def _apply(soup, items):
        for item in items:
            func = resolve(item['func'])
            soup = func(soup, *item.get('args', []))
        return soup

    def _find(self, soup, params):
        if not soup:
            return None
        if type(params) == dict:
            return soup.find(**self._format_params(params))
        if type(params) == list:
            output = soup
            for param in params:
                output = self._find(output, param)
            return output

    def _find_all(self, soup, params):
        output = soup.find(**self._format_params(params))
        while output is not None:
            yield output
            output = output.find_next(**self._format_params(params))

    def get_rows(self):
        strainer = SoupStrainer(**self._format_params(self.config['content']))
        headers = {"Accept-Language": "en-US,en;q=0.5"}
        soup = BeautifulSoup(requests.get(self.link, headers).content, 'lxml', parse_only=strainer)
        return self._find_all(soup, self.config['rows'])

    def get_from_soup(self, soup, detail):
        detail = self.config['find'][detail]
        result = self._find(soup, detail['params'])
        return self._apply(result, detail.get('apply', []))

    @staticmethod
    def _regexp_extract(pattern, string):
        result = pattern.search(string)
        if result:
            return pattern.search(string).group(1)
        else:
            return None

    def _magnify_image(self, image_url):
        output_url = '{0}{1}{2}'.format(
            image_url.split(self.config['images']['split_on'])[0],
            self.config['images']['split_on'][0],
            self.config['images']['version_str']
        )
        return output_url

    def parse_rows(self, rows):

        id_pattern = re.compile(r'/(t{2}\d{7})/')
        year_pattern = re.compile(r'\((\d{4})\)')
        directors_pattern = re.compile(r'li_dr_\d')
        cast_pattern = re.compile(r'li_st_\d')

        for row in rows:

            output = {
                'id': self._regexp_extract(id_pattern, self.get_from_soup(row, 'id')),
                'title': self.get_from_soup(row, 'title'),
                'genre': self.get_from_soup(row, 'genre'),
                'year': self._regexp_extract(year_pattern, self.get_from_soup(row, 'year')),
                'image': self._magnify_image(self.get_from_soup(row, 'image')),
            }

            staff = self.get_from_soup(row, 'staff')
            output.update({'directors': [item.text for item in staff.find_all('a', href=directors_pattern)]})
            output.update({'cast': [item.text for item in staff.find_all('a', href=cast_pattern)]})

            yield output

    def get_results(self):

        rows = self.get_rows()
        parsed_rows = self.parse_rows(rows)
        results = slice(parsed_rows, self.config['nb_results'])

        output = {}
        for result in results:
            output.update({result['id']: result})

        return output
