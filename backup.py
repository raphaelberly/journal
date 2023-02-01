import argparse
import logging
import os

import yaml
import pandas as pd
from app import app, db
from pushover import Client

logging.basicConfig(level='INFO')
LOGGER = logging.getLogger(__name__)

# Create argument parser
parser = argparse.ArgumentParser()
parser.add_argument('--config', '-c', default='config', type=str)
parser.add_argument('--folder', '-f', default='tmp', type=str)

# Parse args
args = parser.parse_args()
credentials = yaml.safe_load(open(f'{args.config}/credentials.yaml'))
table_names = yaml.safe_load(open(f'{args.config}/backup.yaml'))
notifier = Client(**credentials['push'])

# For each target_type type, run the ETL process
fail_list = []
for table_name in table_names:
    try:
        # Fetch table into a Pandas dataframe
        table_ref = f'{credentials["db"]["schema"]}.{table_name}'
        df = pd.read_sql_query(f'SELECT * FROM {table_ref}', db.engine)
        # Backup table as CSV
        backup_path = os.path.join(args.folder, f'{table_name}.csv')
        df.to_csv(backup_path, header=True, index=False)
        LOGGER.info(f'Successful backup of {table_ref} table to: {backup_path}')
    except Exception:
        fail_list.append(table_name)

if fail_list:
    notifier.send_message(
        message=f'Could not backup table{"s" if len(fail_list) > 1 else ""}: {", ".join(fail_list)}',
        title='⚠️ Journal Alert'
    )

LOGGER.info('Done.')
