
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
print(search)
print('CRAWLING TOOK: {} SECONDS'.format(time() - start))
