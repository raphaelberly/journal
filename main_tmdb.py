# -*- coding: utf-8 -*-

import argparse
from time import time
from lib.tmdb import Tmdb


# Create argument parser
parser = argparse.ArgumentParser()
parser.add_argument('--movie', '-m', required=True, help='query string for a movie to look for')

# Parse args
args = parser.parse_args()

start = time()
tmdb = Tmdb()
search = tmdb.search(args.movie)
print(search)

for movie_id in search[:1]:
    print(tmdb.movie(movie_id))

print('Collecting results took: {:.2f} seconds'.format(time() - start))
