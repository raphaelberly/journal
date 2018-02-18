
from app import app
from flask import render_template, redirect, url_for, session
from app.forms import *
from lib.movie import Movie
from lib.view import View


@app.route('/', methods=['GET', 'POST'])
@app.route('/search', methods=['GET', 'POST'])
def search(input=None):
    searchForm = SearchForm()
    moreResultForm = MoreResultForm()

    if searchForm.validate_on_submit():
        view = View(searchForm.input.data, 'config')
        session['input'] = searchForm.input.data
        session['ids'] = view.ids
        movie = Movie(view.ids[0])
        session['movies'] = [movie.to_dict()]
        return render_template('search.html', title='Results page', mode='single',
                               searchForm=searchForm, singleResultForm=moreResultForm)

    if moreResultForm.validate_on_submit():
        if moreResultForm.moreButton.data:
            for id in session.get('ids')[1:5]:
                session['movies'].append(Movie(id).to_dict())
            return render_template('search.html', title='Results page', mode='multiple', searchForm=searchForm)

    return render_template('search.html', title='Search page', searchForm=searchForm)


@app.route('/add/<movie_id>', methods=['GET', 'POST'])
def add(movie_id):

    resultsForm = ResultsForm()
    searchForm = SearchForm()

    return render_template('add.html', title='Search page', resultsForm=resultsForm, searchForm=searchForm,
                           movie_id=movie_id)
