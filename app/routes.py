
from app import app
from flask import render_template, redirect, url_for, session, request
from app.forms import *
from app.models import Record
from lib.movie import Movie
from lib.view import View


@app.route('/', methods=['GET', 'POST'])
@app.route('/search', methods=['GET', 'POST'])
def search():

    searchForm = SearchForm()
    moreResultForm = MoreResultForm()

    if searchForm.validate_on_submit():
        view = View(searchForm.input.data, 'config')
        session['input'] = searchForm.input.data
        session['ids'] = view.ids
        movie = Movie(view.ids[0])
        session['movies'] = [movie.to_dict()]
        return render_template('search.html', mode='single', searchForm=searchForm, singleResultForm=moreResultForm)

    if moreResultForm.validate_on_submit():
        if moreResultForm.moreButton.data:  # Why?
            for id in session.get('ids')[1:5]:
                session['movies'].append(Movie(id).to_dict())
            return render_template('search.html', mode='multiple', searchForm=searchForm)

    return render_template('search.html', searchForm=searchForm)


@app.route('/<movie_id>/add', methods=['GET', 'POST'])
def add(movie_id):

    if movie_id not in session['ids']:
        return redirect(url_for('search'))

    searchForm = SearchForm()
    addForm = AddForm()

    return render_template('add.html', addForm=addForm, searchForm=searchForm, movie_id=movie_id)


@app.route('/<movie_id>/response', methods=['GET', 'POST'])
def respond(movie_id):

    searchForm = SearchForm()
    resultsForm = ResultsForm()

    if movie_id not in session['ids']:
        return redirect(url_for('search'))

    if request.method == 'POST':

        print(request.form)

        if 'gradeRange' in request.form:

            record = Record.query.filter_by(movie=movie_id).first()
            if record:
                return render_template('response.html', resultsForm=resultsForm, searchForm=searchForm,
                                       movie_id=movie_id, grade=record.grade, response='existed')

            grade = float(dict(request.form)['gradeRange'][0])
            print('ADDING MOVIE {0} HERE. GRADE: {1}'.format(movie_id, grade))
            return render_template('response.html', resultsForm=resultsForm, searchForm=searchForm, movie_id=movie_id,
                                   grade=grade, response='added')

        if 'cancelButton' in request.form:
            print('CANCELLING')
            return render_template('response.html', searchForm=searchForm, movie_id=movie_id, response='cancelled')

    return redirect(url_for('search'))
