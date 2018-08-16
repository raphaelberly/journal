# My Movie Journal

_Since January 2014, I have been keeping an Excel log of movies as I watched them, in order to keep track of what I watch and to compute some basic statistics. I recently decided to upgrade it._

This project aims at keeping a journal of the movies I have seen. It takes the form of a Postgres database containing both the logs of all the movies I have seen and [open IMDb data](https://www.imdb.com/interfaces/). This enables me to get a lot of information about the movies I have seen, and also to be able to compute all kinds of useful statistics (proportion of movies watched per genre, favourite directors, actors, writers, etc.)

In order to add movies to the database (with their IMDb ID!) conveniently, whenever I want from my phone or my computer, I also built a simple Flask website, which looks something like this:

<div align="center" border="1px"><img src="img/search_page.png" width="250px"/></div>


### Overview

Hereby the overview of the different sections of the project:

* [1. ETL](#1-etl)
* [2. Search](#2-search)
* [3. Flask App](#3-flask-app)
* [4. Movie Recommendation](#4-movie-recommendation-in-progress)


### 1. ETL

The ETL part of the project aims at inserting the open IMDb data into the database. To do so, one can use the script `main_etl.py`.

Usage example: `python main_etl.py -t titles`

The process is automated on my Raspberry Pi via a cron job, which purpose is to refresh the IMDb data on the database every week (to get updated rankings, new titles, etc.)

The `ETL` class (defined in `lib/etl.py`) is used and the process follows the three inherent steps of an ETL process:

- **Extract:** download the GZIP files from [open IMDb data](https://www.imdb.com/interfaces/), unzip them and split them into chunks. Chunking the file is necessary since the next two steps require the dataset to be loaded into memory (since I run this on my Raspberry Pi, which has little memory).

Then, for each chunk:

- **Transform:** load the chunk in memory and apply transformations, such as filtering, columns renaming, NA handling, etc.
- **Load:** load the resulting dataframe into the database. This process is performed by batch, each of which is loaded to the database using a bulk insert version of pandas `to_sql` function.


### 2. Search

The tricky part, since my Journal is supposed to be working with IMDb data, is to get the IMDb ID of the movies I want to add.

The `Search` class serves that purpose: it scrapes the [Advanced Search](https://www.imdb.com/search/title/form) results page of the IMDb website, for a given input string, and returns a dict containing the list of the results, each result being a dictionary containing ID of the movie, name, year, genres, directors, cast, etc.

`Search` inherits from the `Base` class, which is the base class I use when dealing with web scraping. I designed it to help me manage BeautifulSoup (a very common HTML scraper) via a simple YAML configuration. It is very convenient.

Usage example: `python main_search.py -m "star wars the force awakens"`


### 3. Flask App

At this point, the Journal takes the form of a database containing the open IMDb data, and the movies I watched identified by their IMDb ID, which I can get with the `main_search.py` script. But this is not convenient: I cannot do it from any device, or even from my phone, and more importantly it requires to write an "insert" SQL query.

This is why I built a Flask web-app, which enables me to have a proper interface for searching and adding movies to my journal, from anywhere and without the need to write an SQL query.

The web-app code (routes, HTML templates, CSS code, etc.) can be found in the `app` folder. It is hosted on my Raspberry Pi so I can reach it at any time from my phone or computer.

Here is how it looks like:

<div align="center" border="1px"><img src="img/dual_pages.png" width="500px"/></div>


### 4. Movie Recommendation (in progress)

This is the part of the project I am currently working on.

I have collected a lot of information regarding my tastes, by grading over the last 4 years the ~500 movies I have watched. Joined with all the information that IMDb data can provide, I think that there is a lot I can do:

- find the best movies from genres I appreciate, which I have not watched yet
- find directors or writers that I do not know of but from whom I liked some movies
- train a simple ML model which would predict the grade I would give any movie

I am currently working on a solution to provide a list of recommendations every week, which could be somehow integrated in the web app.

_To be continued..._

