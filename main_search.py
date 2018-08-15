# -*- coding: utf-8 -*-

import argparse
from time import time
from lib.search import Search


# Create argument parser
parser = argparse.ArgumentParser()
parser.add_argument('--movie', '-m', required=True, help='IMDb identifier of the movie')

# Parse args
args = parser.parse_args()

start = time()
search = Search(args.movie).get_results()
print('Collecting results took: {:.2f} seconds'.format(time() - start))
print(search)
