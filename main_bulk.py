
import argparse
from lib.bulk import Bulk

# Create argument parser
parser = argparse.ArgumentParser()
target = parser.add_mutually_exclusive_group(required=True)
target.add_argument('--all', '-a', action='store_true', default=False)
target.add_argument('--types', '-t', nargs='*')

# Parse args
args = parser.parse_args()

# Generate target type list
type_list = ['ratings', 'titles', 'names']
target_types = type_list if args.all else args.types

# For each target type, run the ETL process
for type in target_types:
    assert type in type_list, 'Provided types must be in {}'.format(type_list)
    bulk = Bulk(type)
    file = bulk.extract()
    df = bulk.transform(file)
    bulk.load(df)
