import argparse
import logging
from datetime import datetime
from time import sleep

import yaml
from tqdm import tqdm

from app import db
from app.models import WatchlistItem
from lib.overseerr import Overseerr
from lib.push import Push
from lib.tmdb import Tmdb


LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Create argument parser
parser = argparse.ArgumentParser()
parser.add_argument('--config', '-c', default='config')
args = parser.parse_args()

# Create notification service
credentials = yaml.safe_load(open(f'{args.config}/credentials.yaml'))
notifier = Push(**credentials['push'])

try:
    i = 0
    tmdb = Tmdb(args.config)
    overseerr = Overseerr(args.config)
    LOGGER.info('Update all watchlist items with outdated providers list')

    for item in tqdm(WatchlistItem.query.all()):
        updated_providers = tmdb.providers(item.tmdb_id)
        if overseerr.request_status(item.tmdb_id) == 5:
            updated_providers.append('plex')
        if set(updated_providers) != set(item.providers):
            item.providers = updated_providers
            item.update_datetime_utc = datetime.utcnow()
            # Commit straight away to avoid IdleInTransactionSessionTimeout
            db.session.commit()
            i += 1
        sleep(0.1)

    LOGGER.info(f'Applied {i} changes to the database')

except Exception as e:
    LOGGER.error(str(e))
    notifier.send_message(
        message='An error occurred when updating watchlist providers',
        title='⚠️ Journal Alert'
    )

LOGGER.info('Done')
