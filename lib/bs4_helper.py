from lib.tools import read_config, resolve


class BeautifulSoupHelper(object):

    def __init__(self, config_file):
        self.config = read_config(config_file)

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

    def get_from_soup(self, soup, detail):
        detail = self.config['find'][detail]
        result = self._find(soup, detail['params'])
        return self._apply(result, detail.get('apply', []))
