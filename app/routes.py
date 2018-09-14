import logging

from app import app
from app import db
from datetime import datetime, date
from flask import render_template, session, request
from app.models import Record, Title
from lib.search import Search

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
