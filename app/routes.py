
from app import app
from app import db
from flask import render_template, redirect, url_for, session, request
from app.forms import *
from app.models import Record
from lib.movie import Movie
from lib.view import View


@app.route('/', methods=['GET', 'POST'])
@app.route('/search', methods=['GET', 'POST'])
def search():
    # Instantiate page forms
    searchForm = SearchForm()
    moreResultForm = MoreResultForm()
    # If searchForm is submitted
    if searchForm.validate_on_submit():
        # Get first movie result based on search input
        view = View(searchForm.input.data, 'config')
        session['input'] = searchForm.input.data
        session['ids'] = view.ids
        movie = Movie(view.ids[0])
        session['movies'] = [movie.to_dict()]
        # Render page
        return render_template('search.html', mode='single', searchForm=searchForm, singleResultForm=moreResultForm)
    if moreResultForm.validate_on_submit():
        # If moreButton was clicked
        if moreResultForm.moreButton.data:
            # Add the 4 next movie results based on search input
            for id in session.get('ids')[1:5]:
                session['movies'].append(Movie(id).to_dict())
            # Render page
            return render_template('search.html', mode='multiple', searchForm=searchForm)
    # Else, render a page with only the searchForm
    return render_template('search.html', searchForm=searchForm)


@app.route('/<movie_id>/add', methods=['GET', 'POST'])
def add(movie_id):
    # Check movie was found through search
    if movie_id not in session['ids']:
        return redirect(url_for('search'))
    # Instantiate page forms
    searchForm = SearchForm()
    addForm = AddForm()
    # Render page
    return render_template('add.html', addForm=addForm, searchForm=searchForm, movie_id=movie_id)


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
