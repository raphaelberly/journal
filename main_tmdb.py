# -*- coding: utf-8 -*-

import argparse
from time import time
from lib.tmdb import Tmdb


# Create argument parser
parser = argparse.ArgumentParser()
parser.add_argument('--movie', '-m', required=True, help='query string for a movie to look for')

# Parse args
args = parser.parse_args()

tmdb = Tmdb()
start = time()
search = tmdb.search(args.movie)
print(search)
movies = tmdb.movies(search[:3])
print(movies)

print('Collecting results took: {:.2f} seconds'.format(time() - start))
