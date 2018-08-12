
import argparse
import yaml
from lib.bulk import Bulk

# Create argument parser
parser = argparse.ArgumentParser()
target = parser.add_mutually_exclusive_group(required=True)
target.add_argument('--all', '-a', action='store_true', default=False)
target.add_argument('--types', '-t', nargs='*')
parser.add_argument('--config', '-c', default='config')

# Parse args
args = parser.parse_args()

# Generate target type list
type_list = yaml.load(open('{}/bulk.yaml'.format(args.config)))['definitions'].keys()
target_types = type_list if args.all else args.types

# For each target type, run the ETL process
for type in target_types:
    assert type in type_list, 'Provided types must be in {}'.format(type_list)
    bulk = Bulk(type)
    bulk.etl_by_chunks()
