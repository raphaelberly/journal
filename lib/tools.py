# -*- coding: utf-8 -*-
import os
import shutil
import sys
from datetime import date, timedelta

import yaml


def get_db_uri(type, host, port, db, user, password, **kwargs):
    return f'{type}://{user}:{password}@{host}:{port}/{db}'


def get_db_connection_string(host, port, db, user, password, **kwargs):
    return f"host='{host}' dbname='{db}' port={port} user='{user}' password='{password}'"


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


def get_time_spent_string(minutes):

    timespans = {
        'year': minutes // (60 * 24 * 365),
        'month': minutes % (60 * 24 * 365) // (60 * 24 * 30),
        'day': minutes % (60 * 24 * 30) // (60 * 24),
        'hour': minutes % (60 * 24) // 60,
        'minute': minutes % 60,
    }
    timespans_iter = iter(timespans.items())

    for unit, value in timespans_iter:
        if value == 0:
            continue
        else:
            output = f'{value} {unit}{"s" if value > 1 else ""}'
            try:
                unit, value = next(timespans_iter)
                if value > 0:
                    output += f', {value} {unit}{"s" if value > 1 else ""}'
            except StopIteration:
                pass
            return output
    return '0 minutes'


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
