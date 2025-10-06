from typing import List

from lib.tmdb import Tmdb
from app.models import Rating


class TitleCollector(object):

    def __init__(self):
        self.tmdb = Tmdb()

    def collect(self, title_id: int) -> dict:
        title = self.tmdb.get(title_id).copy()
        imdb_id = title.pop('imdb_id') if 'imdb_id' in title else ''
        if imdb_id:
            result = Rating.query.filter_by(title_id=imdb_id).first()
            if result is not None:
                return {**title, 'imdb_id': imdb_id, 'imdb_rating': result.rating}
        return {**title, 'imdb_id': None, 'imdb_rating': None}

    def collect_bulk(self, title_ids: List[int]) -> List[dict]:
        # Get titles data from TMDb
        titles = self.tmdb.get_bulk(title_ids)
        # For those with an IMDb identifier, fetch rating from DB
        imdb_ids = [title['imdb_id'] for title in titles if title.get('imdb_id')]
        ratings = {item.title_id: item.rating for item in Rating.query.filter(Rating.title_id.in_(imdb_ids)).all()}
        # Gather TMDb and IMDb ratings together
        return [{**title, 'imdb_rating': ratings.get(title.get('imdb_id', 'no_imdb_id'))} for title in titles]
