
import sys
import yaml
import configparser


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
