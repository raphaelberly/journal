# -*- coding: utf-8 -*-
import sys
from datetime import date, datetime, timedelta, UTC

import yaml


def utcnow() -> datetime:
    """Naive UTC timestamp, to match the TIMESTAMP (without time zone) columns of the DDL."""
    return datetime.now(UTC).replace(tzinfo=None)


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
