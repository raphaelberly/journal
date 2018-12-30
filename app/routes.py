import sys

from functools import lru_cache

from app import app
from app import db
from datetime import datetime, date, timedelta
from flask import render_template, session, request
from app.models import Record, Title, Top, Genre, WatchlistItem
from lib.search import Search


CACHE_SIZE = 10


def get_post_result(key):
    return dict(request.form)[key][0]


def get_time_ago_string(dt):

    def get_n_days_ago(n):
        return date.today() - timedelta(days=n)

    if dt >= get_n_days_ago(0):
        return 'Today'

    elif dt >= get_n_days_ago(1):
        return 'Yesterday'

    elif dt >= get_n_days_ago(6):
        return '{0} days ago'.format((date.today() - dt).days)

    elif dt >= get_n_days_ago(27):
        weeks = (date.today() - dt).days // 7
        s = 's' if weeks > 1 else ''
        return '{0} week{1} ago'.format(weeks, s)

    elif dt >= get_n_days_ago(364):
        months = (date.today() - dt).days // 28
        s = 's' if months > 1 else ''
        return '{0} month{1} ago'.format(months, s)

    else:
        years = (date.today() - dt).days // 365
        s = 's' if years > 1 else ''
        return '{0} year{1} ago'.format(years, s)


def remove_from_watchlist(movie_id):
    # Remove from watchlist on database
    to_delete = WatchlistItem.query.filter_by(movie=movie_id).all()
    for record in to_delete:
        db.session.delete(record)
    db.session.commit()
    # Remove from watchlist on session
    session['watchlist'].pop(movie_id)
    session.modified = True


# Cache search results
@lru_cache(CACHE_SIZE)
def get_search_results(input):
    return Search(input, 'config').get_results()


@app.context_processor
def inject_now():
    return {'now': datetime.now()}


@app.route('/recent', methods=['GET', 'POST'])
def recent(nb_movies=25):

    query = db.session \
        .query(Record.date, Record.insert_datetime, Record.grade, Title.title, Title.year, Title.genres) \
        .select_from(Record).join(Record.title) \
        .order_by(Record.date.desc(), Record.insert_datetime.desc())

    show = 'recent'
    if request.method == 'POST':
        if 'show_all' in request.form:
            show = 'all'

    if show == 'recent':
        query = query.limit(nb_movies)

    movies = query.all()
    return render_template('recent.html', title='Recent', movies=movies, show=show, get_time_ago=get_time_ago_string)


@app.route('/statistics', methods=['GET'])
def statistics():

    counts = {}
    # This month's total
    this_month = Record.query \
        .filter(db.extract('year', Record.date) == db.extract('year', date.today())) \
        .filter(db.extract('month', Record.date) == db.extract('month', date.today())) \
        .count()
    counts.update({'this_month': {'count': this_month, 'description': 'movies this month'}})
    # This year's total
    this_year = Record.query \
        .filter(db.extract('year', Record.date) == db.extract('year', date.today())) \
        .count()
    counts.update({'this_year': {'count': this_year, 'description': 'movies this year'}})
    # Number of movies seen in total
    counts.update({'total': {'count': Record.query.count(), 'description': 'movies since January, 2014'}})

    tops = {}
    top_models = {
        'directors': {'model': Top, 'role': 'director', 'min_movie_qty': 3, 'nb_elements': 5},
        'actors': {'model': Top, 'role': 'actor', 'min_movie_qty': 5, 'nb_elements': 5},
        'actresses': {'model': Top, 'role': 'actress', 'min_movie_qty': 4, 'nb_elements': 5},
        'genres': {'model': Genre, 'min_movie_qty': 10, 'nb_elements': 5},
        'composers': {'model': Top, 'role': 'composer', 'min_movie_qty': 4, 'nb_elements': 3}
    }
    for top in top_models:
        model = top_models[top]['model']
        if 'role' in top_models[top].keys():
            values = model.query \
                .filter_by(role=top_models[top]['role']) \
                .filter(model.count >= top_models[top]['min_movie_qty']) \
                .order_by(model.grade.desc(), model.rating.desc()) \
                .all()[:top_models[top]['nb_elements']]
        else:
            values = model.query \
                .filter(model.count >= top_models[top]['min_movie_qty']) \
                .order_by(model.grade.desc(), model.rating.desc()) \
                .all()[:top_models[top]['nb_elements']]
        tops.update({top: values})

    return render_template('statistics.html', title='Statistics', counts=counts, tops=tops)


@app.route('/', methods=['GET', 'POST'])
@app.route('/search', methods=['GET', 'POST'])
def search():

    if request.method == 'POST':
        if 'input' in request.form:

            # Get the results for the provided input
            input = get_post_result('input')
            results = get_search_results(input)

            # Add the grade to the result if the movie was seen already
            records = dict(Record.query.with_entities(Record.movie, Record.grade).all())

            for result in results:
                if records.get(result):
                    results[result].update({'grade': records[result]})

            # Store the results and the input in the session
            session['input'] = input
            session['results'] = results
            return render_template('search.html', title='Search')

    session['input'] = None
    session['results'] = None
    return render_template('search.html', title='Search')


@app.route('/watchlist', methods=['GET', 'POST'])
def watchlist():

    if not request.method == 'POST':
        # Query watchlist on DB
        watchlist_items = WatchlistItem.query.order_by(WatchlistItem.insert_datetime.desc()).all()
        # Format results
        watchlist = {}
        for item in watchlist_items:
            item.__dict__.pop('_sa_instance_state')
            watchlist.update({item.movie: item.__dict__})
        # Update session['watchlist']
        session['watchlist'] = watchlist

    if request.method == 'POST':
        if 'add_to_watchlist' in request.form:
            movie_id = request.args.get('add')
            # Add to watchlist on database
            item = WatchlistItem(insert_datetime=datetime.now(), **session['results'][movie_id])
            db.session.add(item)
            db.session.commit()
            # Add to watchlist on session
            session['watchlist'] = {movie_id: session['results'][movie_id], **session['watchlist']}
            session.modified = True
            return render_template('watchlist.html', title='Watchlist', added=movie_id)

        elif 'remove_from_watchlist' in request.form:
            movie_id = request.args.get('remove')
            remove_from_watchlist(movie_id)
            return render_template('watchlist.html', title='Watchlist', removed=movie_id)

    return render_template('watchlist.html', title='Watchlist')


@app.route('/movie/<movie_id>', methods=['GET', 'POST'])
def movie(movie_id):

    if request.method == 'POST':

        if 'gradeRange' in request.form:

            # Get submitted grade
            grade = float(get_post_result('gradeRange'))

            movie = session['results'][movie_id]
            if movie.get('grade'):
                action = 'updated'
                # Update the movie in the database
                Record.query.filter_by(movie=movie_id).update({'grade': grade})
                db.session.commit()
            else:
                action = 'added'
                # Add the movie to the records database
                record = Record(movie=movie_id, grade=grade)
                db.session.add(record)
                db.session.commit()
                # Remove the movie from the watchlist
                remove_from_watchlist(movie_id)
            # Update the movie item with the grade
            session['results'][movie_id]['grade'] = grade
            session.modified = True
            return render_template('movie.html', title='Movie', movie_id=movie_id,
                                   mode='show_add_or_edit_confirmation', action=action)

        elif 'remove' in request.form:
            # Delete the movie from the database
            to_delete = Record.query.filter_by(movie=movie_id).all()
            for record in to_delete:
                db.session.delete(record)
            db.session.commit()
            # Remove the grade from the movie item
            session['results'][movie_id].pop('grade')
            session.modified = True
            return render_template('movie.html', title='Movie', movie_id=movie_id,
                                   mode='show_remove_confirmation')

    return render_template('movie.html', title='Movie', movie_id=movie_id, mode='show_slider')
