
import os
import requests
import configparser
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine

import logging

logging.basicConfig(level='INFO')
LOGGER = logging.getLogger()


class Bulk:

    def __init__(self, bulk_id, config_folder):
        # Create the config
        self.config = configparser.ConfigParser()
        self.config.read(os.path.join(config_folder, 'bulks.ini'))
        # Create other attributes
        self.bulk_id = bulk_id
        self.date = datetime.now().strftime('%Y%m%d')

    def extract(self):
        LOGGER.info('Downloading {}...'.format(self.bulk_id))
        # Get file name
        file = self.config.get(self.bulk_id, 'file').format(self.date)
        # Execute the request and store result on disk
        data = requests.get(self.config.get(self.bulk_id, 'url'))
        with open(file, 'wb') as f:
            f.write(data.content)
        # Return file path
        return file

    def transform(self, file):
        LOGGER.info('Transforming {}...'.format(self.bulk_id))
        # Create a pandas data frame
        df = pd.read_csv(file, compression='gzip', sep='\t')
        # Keep only useful columns
        cols = ['tconst', 'titleType', 'primaryTitle', 'startYear', 'runtimeMinutes', 'genres']
        df = df[cols]
        # Rename columns
        cols = ['movie', 'type', 'title', 'year', 'duration', 'genres']
        df.columns = cols
        # Filter movies on type
        df = df.loc[df.type.isin(['short', 'movie', 'tvMovie', 'tvShort', 'video'])]
        # Return resulting dataset
        return df

    def load(self, df):
        LOGGER.info('Loading {} to PiDB...'.format(self.bulk_id))
        # Create SQLalchemy engine and replace existing data on the database
        engine = create_engine('postgresql+psycopg2://{0}:{1}@{2}:{3}/{4}').format(
            self.config.get('PI', 'user'),
            self.config.get('PI', 'password'),
            self.config.get('PI', 'host'),
            self.config.get('PI', 'port'),
            self.config.get('PI', 'db'))
        df.to_sql(name='titles', con=engine, schema=self.config.get('PI', 'schema'), index=False, if_exists='replace')


if __name__ == '__main__':

    bulk = Bulk('ratings', 'config')
    # file = bulk.extract()
    df = bulk.transform(file)
    bulk.load(df)
