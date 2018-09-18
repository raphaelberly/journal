import logging

from app import app
from app import db
from datetime import datetime, date, timedelta
from flask import render_template, session, request
from app.models import Record, Title, Top, Genre
from lib.search import Search

LOGGER = logging.getLogger(__name__)


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

    else:
        weeks = (date.today() - dt).days // 7
        s = 's' if weeks > 1 else ''
        return '{0} week{1} ago'.format(weeks, s)


@app.context_processor
def inject_now():
    return {'now': datetime.now()}


@app.route('/recent', methods=['GET'])
def recent(nb_movies=10):
    recent_movies = Record.query.join(Title) \
        .order_by(Record.date.desc(), Record.insert_datetime.desc()) \
        .all()[:nb_movies]
    for movie in recent_movies:
        movie.__setattr__('time_ago', get_time_ago_string(movie.date))
    return render_template('recent.html', title='Recent', recent_movies=recent_movies)


@app.route('/statistics', methods=['GET'])
def statistics(nb_elements=3):

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
        'directors': {'model': Top, 'role': 'director', 'min_movie_qty': 3},
        'actors': {'model': Top, 'role': 'actor', 'min_movie_qty': 5},
        'actresses': {'model': Top, 'role': 'actress', 'min_movie_qty': 4},
        'genres': {'model': Genre, 'min_movie_qty': 10}
    }
    for top in top_models:
        model = top_models[top]['model']
        if 'role' in top_models[top].keys():
            values = model.query \
                .filter_by(role=top_models[top]['role']) \
                .filter(model.count >= top_models[top]['min_movie_qty']) \
                .order_by(model.grade.desc(), model.rating.desc()) \
                .all()[:nb_elements]
        else:
            values = model.query \
                .filter(model.count >= top_models[top]['min_movie_qty']) \
                .order_by(model.grade.desc(), model.rating.desc()) \
                .all()[:nb_elements]
        tops.update({top: values})

    return render_template('statistics.html', title='Statistics', counts=counts, tops=tops)


@app.route('/', methods=['GET', 'POST'])
@app.route('/search', methods=['GET', 'POST'])
def search():

    if request.method == 'POST':
        if 'input' in request.form:

            # Get the results for the provided input
            input = get_post_result('input')
            results = Search(input, 'config').get_results()

            # Add the grade to the result if the movie was seen already
            records = dict(Record.query.with_entities(Record.movie, Record.grade).all())

            for result in results:
                if records.get(result):
                    results[result].update({'grade': records[result]})

            # Store the results and the input in the session
            session['input'] = input
            session['results'] = results

            LOGGER.info('SETTING INPUT TO {}'.format(input))
            return render_template('search.html', title='Search')

    LOGGER.info('SETTING INPUT TO NONE')
    session['input'] = None
    session['results'] = None
    return render_template('search.html', title='Search')


@app.route('/movie/<movie_id>', methods=['GET', 'POST'])
def movie(movie_id):

    # print(request)

    if request.method == 'POST':

        if 'gradeRange' in request.form:

            # Get submitted grade
            grade = float(get_post_result('gradeRange'))

            movie = session['results'][movie_id]
            if movie.get('grade'):
                # Update the movie in the database
                Record.query.filter_by(movie=movie_id).update({'grade': grade})
                db.session.commit()
            else:
                # Add the movie to the database
                record = Record(movie=movie_id, grade=grade)
                db.session.add(record)
                db.session.commit()
            # Update the movie item with the grade
            session['results'][movie_id]['grade'] = grade
            session.modified = True
            return render_template('movie.html', title='Search', movie_id=movie_id, mode='show_add_or_edit_confirmation')

        elif 'remove' in request.form:
            # Delete the movie from the database
            to_delete = Record.query.filter_by(movie=movie_id).all()
            for record in to_delete:
                db.session.delete(record)
            db.session.commit()
            # Remove the grade from the movie item
            session['results'][movie_id].pop('grade')
            session.modified = True
            return render_template('movie.html', title='Search', movie_id=movie_id, mode='show_remove_confirmation')

    return render_template('movie.html', title='Search', movie_id=movie_id, mode='show_slider')
