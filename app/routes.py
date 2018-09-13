import logging

from app import app
from app import db
from datetime import datetime, date
from flask import render_template, redirect, url_for, session, request
from app.models import Record, Title
from lib.search import Search

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


def get_post_result(key):
    return dict(request.form)[key][0]


@app.context_processor
def inject_now():
    return {'now': datetime.now()}


@app.route('/recent', methods=['GET'])
def recent(nb_movies=5):
    recent_movies = Record.query.join(Title) \
        .order_by(Record.date.desc(), Record.insert_datetime.desc()) \
        .all()[:nb_movies]
    return render_template('recent.html', title='Recent', recent_movies=recent_movies)


@app.route('/statistics', methods=['GET'])
def statistics(nb_movies=3):

    # Number of movies seen in total
    metrics = {'total': Record.query.count()}
    # This year's total
    this_year = Record.query \
        .filter(db.extract('year', Record.date) == db.extract('year', date.today())) \
        .count()
    metrics.update({'this_year': this_year})
    # This month's total
    this_month = Record.query \
        .filter(db.extract('year', Record.date) == db.extract('year', date.today())) \
        .filter(db.extract('month', Record.date) == db.extract('month', date.today())) \
        .count()
    metrics.update({'this_month': this_month})

    best_movies = Record.query \
        .filter(db.extract('year', Record.date) == db.extract('year', date.today())) \
        .join(Title) \
        .order_by(Record.grade.desc(), Record.date.desc()) \
        .all()[:nb_movies]

    return render_template('statistics.html', title='Statistics', metrics=metrics, best_movies=best_movies)


@app.route('/', methods=['GET', 'POST'])
@app.route('/search', methods=['GET', 'POST'])
def search():

    if request.method == 'POST':
        if 'input' in request.form:
            input = get_post_result('input')
            results = Search(input, 'config').get_results()
            records = dict(Record.query.with_entities(Record.movie, Record.grade).all())

            session['input'] = input
            session['results'] = results
            # session['records'] = records

            LOGGER.info('SETTING INPUT TO {}'.format(input))
            return render_template('search.html', title='Search', results=results, records=records)

    LOGGER.info('SETTING INPUT TO NONE')
    session['input'] = None
    # session['results'] = None
    return render_template('search.html', title='Search')


@app.route('/movie/<movie_id>', methods=['GET', 'POST'])
def movie(movie_id):

    movie = [item for item in session['results'] if item['id'] == movie_id][0]

    if request.method == 'POST':
        if 'gradeRange' in request.form:
            # Get submitted grade
            grade = float(get_post_result('gradeRange'))
            # Add the movie to the database
            record = Record(movie=movie_id, grade=grade)
            db.session.add(record)
            db.session.commit()
            LOGGER.info('MOVIE {0} GOT GRADE {1}'.format(movie_id, grade))
            return render_template('movie.html', title='Search', movie=movie, mode='show_add_confirmation')
        elif 'cancel' in request.form:
            to_delete = Record.query.filter_by(movie=movie_id).all()
            for record in to_delete:
                db.session.delete(record)
            db.session.commit()
            LOGGER.info('MOVIE {0} REMOVED'.format(movie_id))
            return render_template('movie.html', title='Search', movie=movie, mode='show_cancel_confirmation')

    return render_template('movie.html', title='Search', movie=movie, mode='show_slider')
