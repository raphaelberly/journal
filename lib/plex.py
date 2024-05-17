import os
from typing import List

import cachetools.func
from plexapi.myplex import MyPlexAccount
from plexapi.video import Movie

from lib.tools import read_config


class Plex(object):

    def __init__(self, config_path: str = 'config'):
        _credentials = read_config(os.path.join(config_path, 'credentials.yaml'))['plex']
        self._library = MyPlexAccount(**_credentials).resource('phulos').connect().library.section('Films')

    @staticmethod
    def _get_tmdb_id(movie: Movie) -> int:
        for guid in movie.guids:
            if guid.id.startswith('tmdb://'):
                return int(guid.id[7:])

    @property
    @cachetools.func.ttl_cache(maxsize=1, ttl=10*60)
    def library(self) -> List[int]:
        return [self._get_tmdb_id(movie) for movie in self._library.all()]
