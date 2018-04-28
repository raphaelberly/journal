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
from datetime import datetime
from sqlalchemy import create_engine
from lib.base import Base


logging.basicConfig(level='INFO')
LOGGER = logging.getLogger()


class Bulk(Base):

    def __init__(self, bulk_type, config_folder='config'):
        # Instantiate base
        Base.__init__(self, 'bulk', config_folder)
        # Create other attributes
        self.bulk_type = bulk_type
        self.date = datetime.now().strftime('%Y%m%d')

    def extract(self):
        LOGGER.info('Downloading {}...'.format(self.bulk_type))
        # Get file name
        file = self.config.get('file_path').format(self.bulk_type, self.date)
        # Execute the request and store result on disk
        data = requests.get(self.config.get(self.bulk_type).get('url'))
        with open(file, 'wb') as f:
            f.write(data.content)
        # Return file path
        return file

    def transform(self, file):
        LOGGER.info('Transforming {}...'.format(self.bulk_type))
        # Create a pandas data frame
        df = pd.read_csv(file, compression='gzip', sep='\t')
        # Keep only useful columns
        cols = list(self.config.get(self.bulk_type).get('columns').keys())
        df = df[cols]
        # Rename columns
        cols = [self.config.get(self.bulk_type).get('columns').get(item) for item in cols]
        df.columns = cols
        # Handle null values
        df = df.replace("\\N", np.nan)
        # Apply the filters specified in the config
        filter = self.config.get(self.bulk_type).get('filter')
        if filter:
            for col in filter.keys():
                df = df.loc[df[col].isin(filter.get(col))]
        # Return resulting dataset
        return df

    def load(self, df):
        LOGGER.info('Loading {} to PiDB...'.format(self.bulk_type))
        # Create SQLalchemy engine and replace existing data on the database
        engine = create_engine('postgresql+psycopg2://{0}:{1}@{2}:{3}/{4}'.format(
            self.credentials.get('PI', 'user'),
            self.credentials.get('PI', 'password'),
            self.credentials.get('PI', 'host'),
            self.credentials.get('PI', 'port'),
            self.credentials.get('PI', 'db')))
        params = {'name': self.bulk_type, 'schema': self.credentials.get('PI', 'schema'), 'index': False}
        self._insert_by_chunks(df, engine, 100, params=params)

    def _insert_by_chunks(self, df, engine, nb_chunks, params):
        chunksize = int(len(df) / nb_chunks)
        with tqdm(total=len(df)) as pbar:
            for i, cdf in enumerate(self._chunker(df, chunksize)):
                replace = "replace" if i == 0 else "append"
                cdf.to_sql(con=engine, if_exists=replace, **params)
                pbar.update(chunksize)

    @staticmethod
    def _chunker(seq, size):
        return (seq[pos:pos + size] for pos in range(0, len(seq), size))


if __name__ == '__main__':

    for type in ['ratings', 'titles', 'names']:

        bulk = Bulk(type)
        file = bulk.extract()
        df = bulk.transform(file)
        bulk.load(df)
