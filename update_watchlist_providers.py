import argparse
import logging
from datetime import datetime
from time import sleep

from tqdm import tqdm

from app import db
from app.models import WatchlistItem, Title, User
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

query = db.session.query(WatchlistItem, Title.title, Title.id, User.providers) \
    .select_from(WatchlistItem).join(Title).join(User)

for item, title, tmdb_id, user_providers in tqdm(query.all()):
    updated_providers = [provider for provider in providers.get_names(title, tmdb_id) if provider in user_providers]
    if set(updated_providers) != set(item.providers):
        item.providers = updated_providers
        item.update_datetime_utc = datetime.utcnow()
        i += 1
    sleep(0.5)

LOGGER.info(f'Apply {i} changes to the database')
db.session.commit()

LOGGER.info('Done')
