import argparse
import logging
from datetime import datetime
from time import sleep

from tqdm import tqdm

from app import db
from app.models import WatchlistItem, Title
from lib.tmdb import Tmdb


LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Create argument parser
parser = argparse.ArgumentParser()
parser.add_argument('--config', '-c', default='config')
args = parser.parse_args()

i = 0
tmdb = Tmdb(args.config)
LOGGER.info('Update all watchlist items with outdated providers list')

for item in tqdm(WatchlistItem.query.all()):
    updated_providers = tmdb.providers(item.tmdb_id)
    if set(updated_providers) != set(item.providers):
        item.providers = updated_providers
        item.update_datetime_utc = datetime.utcnow()
        # Commit straight away to avoid IdleInTransactionSessionTimeout
        db.session.commit()
        i += 1
    sleep(0.1)

LOGGER.info(f'Applied {i} changes to the database')

LOGGER.info('Done')
