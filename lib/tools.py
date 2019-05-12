# -*- coding: utf-8 -*-
import sys

import os
import shutil
import yaml
from datetime import date, timedelta
from sqlalchemy import create_engine


def get_database_uri(**params):
    return '{type}://{user}:{password}@{host}:{port}/{db}'.format(**params)


def read_config(path):
    with open(path, 'r') as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            sys.exit(exc)
    return config


def empty_folder(folder):
    if os.path.exists(folder):
        shutil.rmtree(folder)
        os.makedirs(folder)
    else:
        os.makedirs(folder)


def chunk_file(file_path, chunk_size=10**6, header=True):

    folder = os.path.splitext(file_path)[0]
    output_template = os.path.join(folder, '{1}_{0}{2}'.format('{0}', *os.path.splitext(os.path.basename(file_path))))

    empty_folder(folder)

    stream = open(file_path, encoding='utf-8')

    if header:
        header_row = stream.readline()

    writers = {}

    i = 0
    for row in stream:

        j = i // chunk_size + 1
        try:
            writer = writers[j]
        except KeyError:
            new_file_path = output_template.format(j)
            writer = open(new_file_path, 'w+', encoding='utf-8')
            writers[j] = writer
            if header:
                writer.write(header_row)

        writer.write(row)
        i += 1

    return folder


def df_to_table(df, schema, table, if_exists='append', config_folder='config'):

    credentials = read_config(os.path.join(config_folder, 'credentials.yaml'))
    engine = create_engine(get_database_uri(**credentials['pi']))
    params = {'name': table, 'schema': schema, 'index': False}

    df.to_sql(con=engine, if_exists=if_exists, **params)


def get_time_ago_string(dt):

    def get_n_days_ago(n):
        return date.today() - timedelta(days=n)

    if dt >= get_n_days_ago(0):
        return 'Today'

    elif dt >= get_n_days_ago(1):
        return 'Yesterday'

    elif dt >= get_n_days_ago(6):
        return '{0} days ago'.format((date.today() - dt).days)

    elif dt >= get_n_days_ago(27):
        weeks = (date.today() - dt).days // 7
        s = 's' if weeks > 1 else ''
        return '{0} week{1} ago'.format(weeks, s)

    elif dt >= get_n_days_ago(364):
        months = (date.today() - dt).days // 28
        s = 's' if months > 1 else ''
        return '{0} month{1} ago'.format(months, s)

    else:
        years = (date.today() - dt).days // 365
        s = 's' if years > 1 else ''
        return '{0} year{1} ago'.format(years, s)


def resolve(name):
    """
    Copied directly from: https://github.com/python/cpython/blob/master/Lib/logging/config.py
    """
    name = name.split('.')
    used = name.pop(0)
    found = __import__(used)
    for n in name:
        used = used + '.' + n
        try:
            found = getattr(found, n)
        except AttributeError:
            __import__(used)
            found = getattr(found, n)
    return found
