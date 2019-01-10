from datetime import date, datetime
from flask import render_template, request, session, url_for
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import redirect

from app import app
from app import db, login
from app.models import Genre, Record, Title, Top, WatchlistItem, User
from lib.search import Search
from lib.tools import get_time_ago_string


def get_post_result(key):
    return dict(request.form)[key][0]


@app.context_processor
def inject_now():
    return {'now': datetime.now()}


# HANDLE ACME CHALLENGE PROPERLY (FOR HTTPS CERT RENEWAL)
@app.route('/.well-known/acme-challenge/<path:filename>')
def certonly_check(filename):
    return redirect(f'static/.well-known/acme-challenge/{filename}')


# Redirect all auth failures to login page
@login.unauthorized_handler
def unauthorized_callback():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():

    if current_user.is_authenticated:
        return redirect(url_for('search'))

    if request.method == 'POST':
        if 'username' in request.form:
            user = User.query.filter_by(username=get_post_result('username')).first()
            if user is None or not user.check_password(get_post_result('password')):
                return redirect(url_for('login'))
            login_user(user, remember=True)
            return redirect(url_for('search'))

    return render_template('login.html', title='Login')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/recent', methods=['GET', 'POST'])
@login_required
def recent(nb_movies=25):

    query = db.session \
        .query(Record.username, Record.date, Record.insert_datetime, Record.grade, Title.title, Title.year, Title.genres) \
        .select_from(Record).join(Record.title) \
        .filter(Record.username == current_user.username) \
        .order_by(Record.date.desc(), Record.insert_datetime.desc())

    show = 'recent'
    if request.method == 'POST':
        if 'show_all' in request.form:
            show = 'all'

    if show == 'recent':
        query = query.limit(nb_movies)

    movies = query.all()
    return render_template('recent.html', title='Recent', movies=movies, show=show,
                           get_time_ago=get_time_ago_string)


@app.route('/statistics', methods=['GET'])
@login_required
def statistics():

    counts = {}
    # This month's total
    this_month = Record.query \
        .filter_by(username=current_user.username) \
        .filter(db.extract('year', Record.date) == db.extract('year', date.today())) \
        .filter(db.extract('month', Record.date) == db.extract('month', date.today())) \
        .count()
    counts.update({'this_month': {'count': this_month, 'description': 'movies this month'}})
    # This year's total
    this_year = Record.query \
        .filter_by(username=current_user.username) \
        .filter(db.extract('year', Record.date) == db.extract('year', date.today())) \
        .count()
    counts.update({'this_year': {'count': this_year, 'description': 'movies this year'}})
    # Number of movies seen in total
    total = Record.query.filter_by(username=current_user.username).count()
    counts.update({'total': {'count': total, 'description': 'movies since January, 2014'}})

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
                .filter_by(username=current_user.username) \
                .filter_by(role=top_models[top]['role']) \
                .filter(model.count >= top_models[top]['min_movie_qty']) \
                .order_by(model.grade.desc(), model.count.desc(), model.rating.desc()) \
                .all()[:top_models[top]['nb_elements']]
        else:
            values = model.query \
                .filter_by(username=current_user.username) \
                .filter(model.count >= top_models[top]['min_movie_qty']) \
                .order_by(model.grade.desc(), model.count.desc(), model.rating.desc()) \
                .all()[:top_models[top]['nb_elements']]
        tops.update({top: values})

    return render_template('statistics.html', title='Statistics', counts=counts, tops=tops)


@app.route('/', methods=['GET', 'POST'])
@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():

    if request.method == 'POST':
        if 'input' in request.form:

            # Get the results for the provided input
            input = get_post_result('input')
            results = Search(input, 'config').get_results()

            # Add the grade to the result if the movie was seen already
            records = dict(Record.query.with_entities(Record.movie, Record.grade)
                           .filter(Record.username == current_user.username).all())
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


def get_watchlist():
    # Query watchlist on DB
    watchlist_items = WatchlistItem.query \
        .filter_by(username=current_user.username) \
        .order_by(WatchlistItem.insert_datetime.desc()) \
        .all()
    # Format results
    watchlist = {}
    for item in watchlist_items:
        item.__dict__.pop('_sa_instance_state')
        watchlist.update({item.movie: item.__dict__})
    # Return
    return watchlist


def remove_from_watchlist(movie_id):
    # Remove from watchlist on database
    to_delete = WatchlistItem.query.filter_by(movie=movie_id, username=current_user.username).all()
    for record in to_delete:
        db.session.delete(record)
    db.session.commit()


@app.route('/watchlist', methods=['GET', 'POST'])
@login_required
def watchlist():

    if request.method == 'POST':

        if 'add_to_watchlist' in request.form:
            movie_id = request.args.get('add')
            # Add to watchlist on database
            item = WatchlistItem(insert_datetime=datetime.now(), username=current_user.username,
                                 **session['results'][movie_id])
            db.session.add(item)
            db.session.commit()
            # Update watchlist
            watchlist_dict = get_watchlist()
            return render_template('watchlist.html', title='Watchlist', watchlist=watchlist_dict)

        elif 'remove_from_watchlist' in request.form:
            movie_id = request.args.get('remove')
            remove_from_watchlist(movie_id)
            watchlist_dict = get_watchlist()
            return render_template('watchlist.html', title='Watchlist', watchlist=watchlist_dict)

    watchlist_dict = get_watchlist()
    return render_template('watchlist.html', title='Watchlist', watchlist=watchlist_dict)


def get_movie(movie):

    item = {}
    if session.get('results'):
        item = session['results'].get(movie) or {}
    if not item:
        item = WatchlistItem.query \
            .filter_by(username=current_user.username, movie=movie) \
            .order_by(WatchlistItem.insert_datetime.desc()) \
            .first()
        if item:
            item = item.__dict__
            item.pop('_sa_instance_state')
    if not item:
        item = session.get('last_item') or {}

    return item


@app.route('/movie/<movie_id>', methods=['GET', 'POST'])
@login_required
def movie(movie_id):

    # Get movie item
    movie = get_movie(movie_id)
    session['last_item'] = movie

    if request.method == 'POST':

        if 'gradeRange' in request.form:

            # Get submitted grade
            grade = float(get_post_result('gradeRange'))

            if movie.get('grade'):
                action = 'updated'
                # Update the movie in the database
                Record.query \
                    .filter_by(username=current_user.username, movie=movie_id) \
                    .update({'grade': grade})
                db.session.commit()
            else:
                action = 'added'
                # Add the movie to the records database
                record = Record(username=current_user.username, movie=movie_id, grade=grade)
                db.session.add(record)
                db.session.commit()

            # Update movie item
            movie.update({'grade': grade})
            # Update last_item
            session['last_item']['grade'] = grade
            session.modified = True
            # Update the movie item with the grade
            if session.get('results') and (movie_id in session['results']):
                session['results'][movie_id]['grade'] = grade
                session.modified = True
            # Remove from watchlist (if in it)
            remove_from_watchlist(movie_id)

            return render_template('movie.html', title='Movie', item=movie,
                                   mode='show_add_or_edit_confirmation', action=action)

        elif 'remove' in request.form:
            # Delete the movie from the database
            to_delete = Record.query.filter_by(username=current_user.username, movie=movie_id).all()
            for record in to_delete:
                db.session.delete(record)
            db.session.commit()
            # Remove the grade from the movie item
            if session['results'].get('movie_id'):
                session['results'][movie_id].pop('grade')
            session['last_item'].pop('grade')
            session.modified = True
            return render_template('movie.html', title='Movie', item=movie,
                                   mode='show_remove_confirmation')

    return render_template('movie.html', title='Movie', item=movie, mode='show_slider')
