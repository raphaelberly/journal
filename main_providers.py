import argparse
import logging
from time import sleep

from tqdm import tqdm

from app import db
from app.models import WatchlistItem
from lib.providers import Providers


LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Create argument parser
parser = argparse.ArgumentParser()
parser.add_argument('--config', '-c', default='config')
args = parser.parse_args()

i = 0
providers = Providers(config_path=args.config)
LOGGER.info('Update all watchlist items with outdated providers list')
for item in tqdm(WatchlistItem.query.all()):
    updated_providers = providers.get_names(item.title, item.tmdb_id)
    if updated_providers != item.providers:
        item.providers = updated_providers
        i += 1
    sleep(1)

LOGGER.info(f'Apply {i} changes to the database')
db.session.commit()

LOGGER.info('Done')
