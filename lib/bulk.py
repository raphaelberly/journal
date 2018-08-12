# -*- coding: utf-8 -*-

# PATCH FOR PANDAS TO BULK INSERT
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
from .base import Base
from .tools import chunk_file
from sh import gunzip


logging.basicConfig(level='INFO')
LOGGER = logging.getLogger()


class Bulk(Base):

    def __init__(self, bulk_type, config_folder='config'):
        # Instantiate base
        Base.__init__(self, 'bulk', config_folder)
        # Create other attributes
        self.bulk_type = bulk_type
        self.bulk_config = self.config['definitions'][bulk_type]

    def etl_by_chunks(self):

        input_path = self.extract()
        input_path_uncompressed = os.path.splitext(input_path)[0]
        if os.path.exists(input_path_uncompressed):
            os.unlink(input_path_uncompressed)
        gunzip(input_path)

        chunks_folder = chunk_file(input_path_uncompressed)
        chunk_files = os.listdir(chunks_folder)

        i = 1
        for file in chunk_files:
            LOGGER.info('Processing chunk {0} of {1} data'.format(i, self.bulk_type))
            df = self.transform(os.path.join(chunks_folder, file))
            replace = (i == 1)
            self.load(df, replace=replace)
            i += 1

    def extract(self):
        LOGGER.info('Downloading {}...'.format(self.bulk_type))
        # Get file name
        file = self.config['parameters']['file_path'].format(self.bulk_type)
        # Execute the request and store result on disk
        data = requests.get(self.bulk_config['url'])
        with open(file, 'wb') as f:
            f.write(data.content)
        # Return file path
        return file

    def _transform(self, chunk):
        # Keep only useful columns
        cols = list(self.bulk_config['columns'].keys())
        chunk = chunk[cols]
        # Rename columns
        cols = [self.bulk_config['columns'][item] for item in cols]
        chunk.columns = cols
        # Handle null values
        chunk = chunk.replace("\\N", np.nan)
        # Apply the filters specified in the config
        filter = self.bulk_config.get('filter')
        if filter:
            for col in filter.keys():
                chunk = chunk.loc[chunk[col].isin(filter[col])]
        # Return resulting dataset
        return chunk

    def transform(self, file):
        LOGGER.info('Transforming data...')
        # Create a pandas data frame by chunks
        df = pd.read_csv(file, sep='\t')
        return self._transform(df)

    def load(self, df, replace=False):
        LOGGER.info('Loading data to the database...')
        # Create SQLalchemy engine and replace existing data on the database
        engine = create_engine('postgresql+psycopg2://{0}:{1}@{2}:{3}/{4}'.format(
            self.credentials.get('PI', 'user'),
            self.credentials.get('PI', 'password'),
            self.credentials.get('PI', 'host'),
            self.credentials.get('PI', 'port'),
            self.credentials.get('PI', 'db')))
        params = {'name': self.bulk_type, 'schema': self.credentials.get('PI', 'schema'), 'index': False}
        # Empty the table if replace == True
        if replace:
            self._empty_table(engine, self.credentials.get('PI', 'schema'), self.bulk_type)
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
    def _empty_table(sqlalchemy_engine, schema, table):
        connection = sqlalchemy_engine.connect()
        transaction = connection.begin()
        LOGGER.info('Emptying table {0}.{1}'.format(schema, table))
        try:
            connection.execute('DELETE FROM {0}.{1}'.format(schema, table))
            transaction.commit()
        except:
            transaction.rollback()
            raise
