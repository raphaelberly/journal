import argparse
import logging
from time import sleep

from app import db
from app.models import Record, User
from lib.tmdb import Tmdb
from lib.tools import read_config


LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Create argument parser
parser = argparse.ArgumentParser()
parser.add_argument('--user', '-u', required=True, help='name of the used whose watchlist is being filled')
parser.add_argument('--movies', '-m', required=True, help='path to a YAML file containing a list of all movies to add')

# Parse args
args = parser.parse_args()

# Initialisation
tmdb = Tmdb()
titles = read_config(args.movies)

# Check that provided user exists
assert User.query.filter_by(username=args.user).count() > 0, 'Provided user is unknown'

i = 0
LOGGER.info('Loading movies to database')
# Iterate through watchlist and add each item
for title in titles:
    results, _ = tmdb.search_movies(title['title'], 1)
    try:
        movie = results[0]
    except IndexError:
        LOGGER.error(f'Could not find movie for query: "{title["title"]}"')
    else:
        if abs(int(movie['year']) - title['year']) > 1:
            LOGGER.error(f'Could not insert "{title["title"]}": found year {movie["year"]} instead of {title["year"]}')
            continue
        if Record.query.filter_by(username=args.user, movie=movie['movie']).count() == 0:
            item = Record(username=args.user, movie=movie['movie'], tmdb_id=movie['tmdb_id'], grade=title['grade'])
            item.date = title['date']
            db.session.add(item)
            i += 1
            LOGGER.debug(f'Movie inserted. Query: "{title}" | Result: "{movie["title"]} ({movie["year"]})"')
        else:
            LOGGER.warning(f'Skipped movie "{title}": "{movie["title"]} ({movie["year"]})" already in watchlist')
    finally:
        sleep(0.2)

# Commit changes
db.session.commit()
LOGGER.info(f'Inserted {i} movies')
LOGGER.info(f'Done')
