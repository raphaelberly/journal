
import sys
import yaml
import configparser


def read_config(path):
    with open(path, 'r') as stream:
        try:
            config = yaml.load(stream)
        except yaml.YAMLError as exc:
            sys.exit(exc)
    return config


def read_credentials(path):
    credentials = configparser.ConfigParser()
    credentials.read(path)
    return credentials
