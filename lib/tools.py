import configparser
import os
import shutil
import sys

import yaml


def read_credentials(path):
    credentials = configparser.ConfigParser()
    credentials.read(path)
    return credentials


def get_database_uri(credentials):
    return 'postgresql+psycopg2://{0}:{1}@{2}:{3}/{4}'.format(
        credentials.get('PI', 'user'),
        credentials.get('PI', 'password'),
        credentials.get('PI', 'host'),
        credentials.get('PI', 'port'),
        credentials.get('PI', 'db')
    )


def read_config(path):
    with open(path, 'r') as stream:
        try:
            config = yaml.load(stream)
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

    stream = open(file_path)

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
            writer = open(new_file_path, 'w+')
            writers[j] = writer
            if header:
                writer.write(header_row)

        writer.write(row)
        i += 1

    return folder
