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
        detail = self.config['find'][detail]
        soup = self._remove(soup, detail.get('remove'))
        soup = self._find(soup, detail.get('params'))
        soup = self._format(soup, detail.get('format'))
        soup = self._strip(soup, detail.get('strip'))
        return soup

    def format_params(self, params):
        assert 'tag' in params, "'tag' key must be in {}".format(params)
        if params.get('type') and params.get('key'):
            return {'name': params.get('tag'), 'attrs': {params.get('type'): params.get('key')}}
        else:
            return {'name': params.get('tag')}

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
        if type(params) == dict:
            if isinstance(soup, list):
                output = []
                for broth in soup:
                    if params.get('multiple'):
                        [output.append(item) for item in broth.findAll(**self.format_params(params))]
                    output.append(broth.find(**self.format_params(params)))
                return output
            else:
                if params.get('multiple'):
                    return soup.findAll(**self.format_params(params))
                return soup.find(**self.format_params(params))
        if type(params) == list:
            if isinstance(soup, list):
                output = []
                for broth in soup:
                    # Apply the filter one after the other
                    for param in params:
                        broth = self._find(broth, param)
                    output.extend(broth)
            else:
                output = soup
                # Apply the filter one after the other
                for param in params:
                    output = self._find(output, param)
            return output

    @staticmethod
    def _format(input, format):
        if format:
            if format == 'text':
                if isinstance(input, list):
                    return [item.text for item in input]
                return input.text
            elif format == 'image':
                if isinstance(input, list):
                    return [item['src'] for item in input]
                return input['src']
            elif format == 'link':
                if isinstance(input, list):
                    return [item['href'] for item in input]
                return input['href']
            else:
                raise Exception('Unknown output type: {}'.format(format))
        return input

    @staticmethod
    def _strip(input, strip):
        if strip:
            if isinstance(input, list):
                return [item.strip(strip) for item in input]
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
