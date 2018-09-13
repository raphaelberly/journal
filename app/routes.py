
from app import app
from app import db
from datetime import datetime, date
from flask import render_template, redirect, url_for, session, request
from app.forms import *
from app.models import Record, Title
from lib.search import Search


def get_post_result(key):
    return dict(request.form)[key][0]


@app.context_processor
def inject_now():
    return {'now': datetime.now()}


@app.route('/', methods=['GET', 'POST'])
@app.route('/search', methods=['GET', 'POST'])
def search():
    # Instantiate page forms
    searchForm = SearchForm()
    moreResultForm = MoreResultForm()
    # If searchForm is submitted
    if searchForm.validate_on_submit():
        # Get first movie result based on search input
        results = Search(searchForm.input.data, 'config').get_results()
        if results:
            session['results'] = results
            session['ids'] = [result['id'] for result in session['results']]
            session['movies'] = [session['results'][0]]
            # Render page
            return render_template('search.html', mode='single', searchForm=searchForm, singleResultForm=moreResultForm)
        else:
            session['results'] = None
            session['ids'] = None
            session['movies'] = None
            return render_template('search.html', mode='none', searchForm=searchForm)
    if moreResultForm.validate_on_submit():
        # If moreButton was clicked
        if moreResultForm.moreButton.data:
            # Add the next movie results based on search input
            session['movies'] = session['results']
            # Render page
            return render_template('search.html', mode='multiple', searchForm=searchForm)
    # Else, render a page with only the searchForm
    return render_template('search.html', searchForm=searchForm)


@app.route('/<movie_id>/add', methods=['GET', 'POST'])
def add(movie_id):
    # Check movie was found through search
    if movie_id not in session['ids']:
        return redirect(url_for('search'))
    movie = [item for item in session['movies'] if item['id'] == movie_id][0]
    # Instantiate page forms
    searchForm = SearchForm()
    addForm = AddForm()
    # Render page
    return render_template('add.html', addForm=addForm, searchForm=searchForm, movie=movie)


@app.route('/<movie_id>/response', methods=['GET', 'POST'])
def respond(movie_id):
    # Instantiate forms
    searchForm = SearchForm()
    resultsForm = ResultsForm()
    # Check movie was found through search
    if movie_id not in session['ids']:
        return redirect(url_for('search'))
    # If there was a post request
    if request.method == 'POST':
        # If a grade was submitted
        if 'gradeRange' in request.form:
            # If movie already in db, return 'existed' response page
            record = Record.query.filter_by(movie=movie_id).first()
            if record:
                return render_template('response.html', resultsForm=resultsForm, searchForm=searchForm,
                                       movie_id=movie_id, grade=record.grade, response='existed')
            # Else, add movie to db and return 'added' response page
            grade = float(dict(request.form)['gradeRange'][0])
            # Add the movie to the database
            record = Record(movie=movie_id, grade=grade)
            db.session.add(record)
            db.session.commit()
            # Render response template
            return render_template('response.html', resultsForm=resultsForm, searchForm=searchForm, movie_id=movie_id,
                                   grade=grade, response='added')
        # If cancel button was clicked
        if 'cancelButton' in request.form:
            # Remove movie from db
            to_delete = Record.query.filter_by(movie=movie_id).all()
            for record in to_delete:
                db.session.delete(record)
            db.session.commit()
            # Render 'cancelled' response page
            return render_template('response.html', searchForm=searchForm, movie_id=movie_id, response='cancelled')
    # Else, redirect to search page
    return redirect(url_for('search'))


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


@app.route('/search2', methods=['GET', 'POST'])
def search2():

    if request.method == 'POST':
        if 'input' in request.form:
            input = get_post_result('input')
            results = Search(input, 'config').get_results()
            records = dict(Record.query.with_entities(Record.movie, Record.grade).all())

            # session['input'] = input
            # session['results'] = results
            # session['records'] = records

            print('SETTING INPUT TO {}'.format(input))
            return render_template('search2.html', title='Search', input=input, results=results, records=records)

    print('INPUT NOT SET')
    return render_template('search2.html', title='Search')
