
from app import app
from flask import render_template, flash, redirect, url_for
from app.forms import *
from lib.movie import Movie
from lib.view import View


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home page')


@app.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    if form.validate_on_submit():
        view = View(form.input.data, 'config')
        movies = []
        for id in view.ids[:3]:
            movie = Movie(id)
            movies.append(movie)
        return render_template('search.html', title='Results page', form=form, results=movies)
    return render_template('search.html', title='Search page', form=form)
