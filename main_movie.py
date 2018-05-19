
import argparse
from time import time
from lib.movie import Movie


# Create argument parser
parser = argparse.ArgumentParser()
parser.add_argument('--movie', '-m', required=True, help='IMDb identifier of the movie')

# Parse args
args = parser.parse_args()

start = time()
test = Movie(args.movie)
print('TOOK: {} s'.format(time()-start))

print(test.get('title'))
print(test.get('year'))
print(test.get('director'))
print(test.get('actors'))
print(test.get('poster'))
