import csv
import gzip
import logging
import os
from csv import DictReader
from functools import partial

import numpy as np
import psycopg2
import requests
from sqlalchemy import text
from toolz import partition_all
from tqdm import tqdm

from lib.tools import read_config, get_db_connection_string

logging.basicConfig(level='INFO')
LOGGER = logging.getLogger()


class ETL:

    def __init__(self, target_type, config_folder='config'):
        self.config = read_config(os.path.join(config_folder, 'etl.yaml'))
        self._credentials = read_config(os.path.join(config_folder, 'credentials.yaml'))
        self.target_type = target_type
        self.table_name = f'imdb.{target_type}'
        self.etl_config = self.config['definitions'][target_type]

    def extract(self, use_cache=False):
        file_path = self.config['parameters']['file_path'].format(self.target_type)
        cache_path = file_path + '.cache'
        if use_cache and os.path.exists(cache_path):
            LOGGER.info(f'Using cached file: {cache_path}...')
            return cache_path
        else:
            LOGGER.info(f'Downloading {self.target_type}...')
            url = self.etl_config['url']
            self._download_file(url, file_path)
            return file_path

    @staticmethod
    def _download_file(url, file_path, block_size=10**6):
        r = requests.get(url, stream=True)
        total_size = int(r.headers.get('content-length', 0))
        with open(file_path, 'wb') as f:
            for chunk in tqdm(r.iter_content(block_size), total=np.ceil(total_size/block_size), unit='MB'):
                f.write(chunk)

    def run(self, use_cache=False):
        # Extract data
        filepath = self.extract(use_cache=use_cache)
        # Process extracted data
        stream = gzip.open(filepath, 'rt')
        rows = DictReader(stream, delimiter='\t', quoting=csv.QUOTE_NONE)
        # Apply filters when applicable
        if self.etl_config.get('filter'):
            for col_name, col_values in self.etl_config['filter'].items():
                rows = filter(lambda row: row[col_name] in col_values, rows)
        rows = map(self._rename_columns, rows)
        # Upload to db
        with psycopg2.connect(get_db_connection_string(**self._credentials['db'])) as conn:
            self.to_db(conn, rows, 1000)
        # If a new file was downloaded and nothing went wrong, cache it
        if not filepath.endswith('.cache'):
            os.rename(filepath, filepath + '.cache')

    def _rename_columns(self, row):
        new_dict = {}
        for colname, new_colname in self.etl_config['columns'].items():
            if row[colname] != "\\N":
                new_dict[new_colname] = row[colname]
        return new_dict

    def _truncate_table(self, conn):
        cur = conn.cursor()
        cur.execute(text(f'TRUNCATE TABLE {self.table_name};'))
        cur.close()

    @staticmethod
    def _get_insert_query(table_name, row):
        key_str = ','.join(row.keys())
        val_str = "'{}'".format("','".join((str(val).replace("'", "''") for val in row.values())))
        return f'INSERT INTO {table_name} ({key_str}) VALUES ({val_str});'

    def to_db(self, conn,  rows, batch_size=1):
        # Truncate table
        self._truncate_table(conn)
        # Take care of logging
        LOGGER.info('Uploading to database...')
        tqdm_kwargs = {'desc': '> processed', 'unit': ' rows', 'mininterval': 1}
        tqdm_values_generator = tqdm(rows, **tqdm_kwargs)
        # Insert values by batch
        _get_insert_query = partial(self._get_insert_query, self.table_name)
        query_generator = map(_get_insert_query, tqdm_values_generator)
        query_batch_generator = partition_all(batch_size, query_generator)
        i = 0
        for query_batch in query_batch_generator:
            cur = conn.cursor()
            cur.execute(text('\n'.join(query_batch)))
            cur.close()
            i += len(query_batch)
        LOGGER.info(f'{i} rows were processed and sent to database')
