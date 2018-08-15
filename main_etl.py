# -*- coding: utf-8 -*-

import argparse
import yaml
from lib.etl import ETL

# Create argument parser
parser = argparse.ArgumentParser()
target = parser.add_mutually_exclusive_group(required=True)
target.add_argument('--all', '-a', action='store_true', default=False)
target.add_argument('--types', '-t', nargs='*')
parser.add_argument('--config', '-c', default='config')

# Parse args
args = parser.parse_args()

# Generate target_type type list
type_list = yaml.load(open('{}/etl.yaml'.format(args.config)))['definitions'].keys()
target_types = type_list if args.all else args.types

# For each target_type type, run the ETL process
for target_type in target_types:
    assert target_type in type_list, 'Provided types must be in {}'.format(type_list)
    etl = ETL(target_type)
    etl.run()
