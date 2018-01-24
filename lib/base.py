# -*- coding: utf-8 -*-

import os
import sys
import yaml
import requests
import configparser
from bs4 import BeautifulSoup


class Base:

    def __init__(self, base_type, config_folder):

        self._base_type = base_type
        self.config = self.read_config(os.path.join(config_folder, '{}.yaml'.format(base_type)))
        self.credentials = self.read_credentials(os.path.join(config_folder, 'credentials.ini'))

    def get_detail(self, link, detail):
        soup = BeautifulSoup(requests.get(link).content, "html.parser")
        soup = self._remove(soup, self.config['find'][detail].get('remove'))
        soup = self._find(soup, self.config['find'][detail].get('params'))
        soup = self._format(soup, self.config['find'][detail].get('format'))
        soup = self._strip(soup, self.config['find'][detail].get('strip'))
        return soup

    def format_params(self, params):
        return {'name': params.get('tag'), 'attrs': {params.get('type'): params.get('key')}}

    def _remove(self, soup, remove):
        if remove:
            if type(remove) == str:
                soup.find(remove).extract()
            if type(remove) == dict:
                soup.find(**self.format_params(remove)).extract()
            if type(remove) == list:
                # Remove each of the items of the to_remove list
                for item in remove:
                    soup.find(**self.format_params(item)).extract()
        return soup

    def _find(self, soup, params):
        if type(params) == str:
            return soup.find(params)
        if type(params) == dict:
            return soup.find(**self.format_params(params))
        if type(params) == list:
            aux = soup
            # Apply the filter one after the other
            for param in params:
                aux = self._find(aux, param)
            return aux

    @staticmethod
    def _format(input, format):
        if format:
            if format == 'text':
                return input.text
            elif format == 'image':
                return input['src']
            elif format == 'link':
                return input['href']
            else:
                raise Exception('Unknown output type: {}'.format(format))
        return input

    @staticmethod
    def _strip(input, strip):
        if strip:
            assert type(input) == str, 'Type of input should be str to strip. Current: {}'.format(type(input))
            return input.strip(strip)
        return input

    @staticmethod
    def read_config(path):
        with open(path, 'r') as stream:
            try:
                config = yaml.load(stream)
            except yaml.YAMLError as exc:
                sys.exit(exc)
        return config

    @staticmethod
    def read_credentials(path):
        credentials = configparser.ConfigParser()
        credentials.read(path)
        return credentials
