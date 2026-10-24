import json
import os
from time import monotonic

import requests

from lib.tools import read_config


class Overseerr(object):

    BASE_URL = 'https://request.teulon.eu:443/api/v1/'
    HEADERS = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
    }
    DEFAULT_REQUEST_NB = 200
    # Do not retry to log in more than once every RETRY_AFTER_SECONDS: the app is long-lived
    # and Overseerr may be down for a while
    RETRY_AFTER_SECONDS = 300
    # The whole library (~1 MB) is listed once a day, and the last RECENT_REQUEST_NB requests of the account on each
    # lookup: a request becoming available shows at once, a movie added on Plex by someone else the next day
    LIBRARY_MAX_AGE_SECONDS = 24 * 60 * 60
    RECENT_REQUEST_NB = 10

    def __init__(self, config_path: str = 'config'):
        self._credentials = read_config(os.path.join(config_path, 'credentials.yaml'))['overseerr']
        self.session = requests.Session()
        self.account_id = None
        self._is_available = False
        self._last_login_attempt = None
        self._library = set()
        self._library_read_at = None
        self._login()

    @property
    def is_available(self) -> bool:
        # Overseerr may have come back up since the last attempt, so retry (at most one call
        # every RETRY_AFTER_SECONDS) instead of staying down until the app is restarted
        return self._login()

    def _login(self) -> bool:
        # Nothing to do while the session is known to work
        if self._is_available:
            return True
        # Back off between two failed attempts
        now = monotonic()
        if self._last_login_attempt is not None and now - self._last_login_attempt < self.RETRY_AFTER_SECONDS:
            return False
        self._last_login_attempt = now
        # Try to open a new session
        try:
            response = self.session.post(
                self.BASE_URL + 'auth/local', data=json.dumps(self._credentials), headers=self.HEADERS
            )
            # If no ConnectionError was raised but status >= 300, raise it
            if response.status_code >= 300:
                raise requests.exceptions.ConnectionError
            self.account_id = json.loads(response.content)['id']
        except (requests.exceptions.RequestException, KeyError, ValueError):
            self._is_available = False
            self.account_id = None
        else:
            self._is_available = True
        return self._is_available

    def _get(self, query: str):
        # Flag the service as unavailable if it went down since the session was opened
        try:
            return json.loads(self.session.get(self.BASE_URL + query).content)
        except (requests.exceptions.RequestException, ValueError):
            self._is_available = False
            return None

    def request_status(self, tmdb_id: int) -> int:
        response = self._get(f'movie/{tmdb_id}')
        try:
            return response['mediaInfo']['status']
        except (KeyError, TypeError):
            return -1

    def request_statuses(self, take: int = DEFAULT_REQUEST_NB) -> dict:
        query = f'request?take={take}&requestedBy={self.account_id}&skip=0&sort=added'
        response = self._get(query)
        if response is None:
            return {}
        output = {}
        for item in response.get('results', []):
            # Skip the TV shows, whose ids may match a movie's
            if item['type'] != 'movie':
                continue
            if item['status'] < 2:
                output[item['media']['tmdbId']] = item['status']
            else:
                output[item['media']['tmdbId']] = item['media']['status']
        return output

    def available_movies(self) -> set:
        # List the whole library when the last list is a day old, in one page. TV shows are listed too, with ids of
        # their own that may match a movie's. Keep the last list if the call fails
        if self._library_read_at is None or monotonic() - self._library_read_at > self.LIBRARY_MAX_AGE_SECONDS:
            response = self._get('media?filter=available&take=10000&skip=0')
            if response is not None and 'results' in response:
                self._library = {item['tmdbId'] for item in response['results'] if item['mediaType'] == 'movie'}
                self._library_read_at = monotonic()
        # The last requests of the account are fresher than the library: let their status win
        available = set(self._library)
        for tmdb_id, status in self.request_statuses(self.RECENT_REQUEST_NB).items():
            if status == 5:
                available.add(tmdb_id)
            else:
                available.discard(tmdb_id)
        return available

    def request_title(self, tmdb_id: int) -> None:
        payload = {'mediaId': tmdb_id, 'mediaType': 'movie', 'is4k': False}
        try:
            self.session.post(self.BASE_URL + 'request', data=json.dumps(payload), headers=self.HEADERS)
        except requests.exceptions.RequestException:
            self._is_available = False
