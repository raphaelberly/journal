# -*- coding: utf-8 -*-

# PATCH FOR PANDAS TO BULK INSERT
# Thanks to this piece of code, pandas to_sql function performance is improved a lot (~ *5)
# Source: https://stackoverflow.com/questions/40119805/pandas-to-sql-with-sqlalchemy-and-psql-never-finishes
from pandas.io.sql import SQLTable
def _execute_insert(self, conn, keys, data_iter):
    data = [dict((k, v) for k, v in zip(keys, row)) for row in data_iter]
    conn.execute(self.insert_statement().values(data))
SQLTable._execute_insert = _execute_insert

import os
import logging
import requests
import numpy as np
import pandas as pd
from tqdm import tqdm
from sqlalchemy import create_engine
from .tools import chunk_file, get_database_uri, read_config
from sh import gunzip


logging.basicConfig(level='INFO')
LOGGER = logging.getLogger()


class ETL:

    def __init__(self, target_type, config_folder='config'):
        self.config = read_config(os.path.join(config_folder, 'etl.yaml'))
        self.credentials = read_config(os.path.join(config_folder, 'credentials.yaml'))
        self.target_type = target_type
        self.etl_config = self.config['definitions'][target_type]

    def run(self):
        # Extract data (as chunks)
        chunk_files = self.extract()
        i = 1
        for file in chunk_files:
            # Transform each chunk and load it to the database
            LOGGER.info('Processing chunk {0} of {1} data'.format(i, self.target_type))
            df = self.transform(file)
            replace = (i == 1)
            self.load(df, replace=replace)
            i += 1

    def extract(self):
        LOGGER.info('Downloading {}...'.format(self.target_type))
        # Download file
        file_path = self.config['parameters']['file_path'].format(self.target_type)
        data = requests.get(self.etl_config['url'])
        with open(file_path, 'wb') as f:
            f.write(data.content)
        # Uncompress downloaded file
        uncompressed_file_path = os.path.splitext(file_path)[0]
        if os.path.exists(uncompressed_file_path):
            os.unlink(uncompressed_file_path)
        gunzip(file_path)
        # Split resulting file into chunks
        chunks_folder = chunk_file(uncompressed_file_path)
        # Return the chunk paths list
        return sorted([os.path.join(chunks_folder, file) for file in os.listdir(chunks_folder)])

    def transform(self, file):
        LOGGER.info('Transforming data...')
        # Create a pandas data frame by chunks
        chunk = pd.read_csv(file, sep='\t')
        # Keep only useful columns
        cols = list(self.etl_config['columns'].keys())
        chunk = chunk[cols]
        # Rename columns
        cols = [self.etl_config['columns'][item] for item in cols]
        chunk.columns = cols
        # Handle null values
        chunk = chunk.replace("\\N", np.nan)
        # Apply the filters specified in the config
        filter = self.etl_config.get('filter')
        if filter:
            for col in filter.keys():
                chunk = chunk.loc[chunk[col].isin(filter[col])]
        # Return resulting dataset
        return chunk

    def load(self, df, replace=False):
        LOGGER.info('Loading data to the database...')
        # Create SQLalchemy engine and replace existing data on the database
        engine = create_engine(get_database_uri(**self.credentials['pi']))
        schema = self.credentials['pi']['schema']
        params = {'name': self.target_type, 'schema':schema, 'index': False}
        # Empty the table if replace == True
        if replace:
            self._empty_table(engine, schema, self.target_type)
        # Insert by batch
        self._insert_by_batch(df, engine, 100, params=params)

    def _insert_by_batch(self, df, engine, nb_batches, params):
        batch_size = int(len(df) / nb_batches)
        with tqdm(total=len(df)) as pbar:
            for i, cdf in enumerate(self._batcher(df, batch_size)):
                cdf.to_sql(con=engine, if_exists='append', **params)
                pbar.update(batch_size)

    @staticmethod
    def _batcher(seq, size):
        return (seq[pos:pos + size] for pos in range(0, len(seq), size))

    @staticmethod
    def _empty_table(engine, schema, table):
        connection = engine.connect()
        transaction = connection.begin()
        LOGGER.info('Emptying table {0}.{1}'.format(schema, table))
        try:
            connection.execute('DELETE FROM {0}.{1}'.format(schema, table))
            transaction.commit()
        except:
            transaction.rollback()
            raise
