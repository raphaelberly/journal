import argparse
import logging
import os
from datetime import datetime

import yaml
import pandas as pd
from sqlalchemy import text

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

# Create a dated folder
folder_path = os.path.join(args.folder, datetime.today().strftime('%Y-%m-%d'))
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

# Backup each table
fail_list = []
for table_name in table_names:
    try:
        # Fetch table into a Pandas dataframe
        table_ref = f'{credentials["db"]["schema"]}.{table_name}'
        df = pd.read_sql_query(text(f'SELECT * FROM {table_ref}'), db.engine.connect())
        # Backup table as CSV
        backup_path = os.path.join(folder_path, f'{table_name}.csv')
        df.to_csv(backup_path, header=True, index=False)
        LOGGER.info(f'Successful backup of {table_ref} table to: {backup_path}')
    except Exception as e:
        fail_list.append(table_name)
        LOGGER.error(str(e))

if fail_list:
    notifier.send_message(
        message=f'Could not backup table{"s" if len(fail_list) > 1 else ""}: {", ".join(fail_list)}',
        title='⚠️ Journal Alert'
    )
