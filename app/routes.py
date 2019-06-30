from copy import deepcopy
from datetime import date, datetime, timedelta
from flask import render_template, request, url_for
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import func
from werkzeug.utils import redirect

from app import app
from app import db, login
from app.forms import RegistrationForm
from app.models import Record, Title, Top, WatchlistItem, User
from lib.tmdb import Tmdb
from lib.tools import get_time_ago_string

tmdb = Tmdb()


def get_post_result(key):
    return dict(request.form)[key][0]


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
            login_user(user, remember=True, duration=timedelta(days=90))
            return redirect(url_for('search'))

    return render_template('login.html', title='Login')


@app.route('/signin', methods=['GET', 'POST'])
def signin():

    if current_user.is_authenticated:
        return redirect(url_for('search'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user, remember=True, duration=timedelta(days=90))
        return redirect(url_for('search'))

    return render_template('signin.html', title='Sign in', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/recent', methods=['GET'])
@login_required
def recent():

    nb_recent = Record.query \
        .filter(Record.username == current_user.username) \
        .filter(Record.recent == True) \
        .count()

    query = db.session \
        .query(Record.username, Record.date, Record.tmdb_id, Record.insert_datetime, Record.grade,
               Title.title, Title.year, Title.genres) \
        .select_from(Record).join(Record.title) \
        .filter(Record.username == current_user.username) \
        .filter(Record.recent == True) \
        .order_by(Record.date.desc(), Record.insert_datetime.desc())

    if not request.args.get('show_all'):
        query = query.limit(25)

    movies = query.all()
    show_button = nb_recent > len(movies)
    scroll = int(request.args.get('scroll', 0))

    return render_template('recent.html', title='Recent', movies=movies, show_button=show_button,
                           get_time_ago=get_time_ago_string, scroll=scroll)


def get_number_suffix(number):
    if 10 <= number % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(number % 10, 'th')
    return suffix


def add_rank_and_suffix(item, rank):
    item = item._asdict()
    item['rank'] = rank
    item['suffix'] = get_number_suffix(rank)
    return item


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
    start_date = db.session.query(func.min(Record.date))\
        .filter(Record.username == current_user.username).scalar()
    total_description = f'movies since {start_date.strftime("%B, %Y")}' if start_date else 'in total'  # no if >> crash
    counts.update({'total': {'count': total, 'description': total_description}})

    # Year applicable = this year if today > January 31st, else last year
    year_applicable = (date.today() - timedelta(days=31)).year
    if year_applicable == date.today().year:
        total_applicable = this_year
    else:
        total_applicable = Record.query \
            .filter_by(username=current_user.username) \
            .filter(db.extract('year', Record.date) == year_applicable) \
            .count()
    # Query best and worst movies from applicable year
    query = db.session \
        .query(Record.username, Record.date, Record.tmdb_id, Record.grade,
               Title.title, Title.year, Title.genres) \
        .select_from(Record).join(Record.title) \
        .filter(Record.username == current_user.username) \
        .filter(db.extract('year', Record.date) == year_applicable)
    best = query.order_by(Record.grade.desc(), Record.insert_datetime.desc()).limit(3).all()
    worst = query.order_by(Record.grade, Record.insert_datetime.desc()).limit(3).all()
    # Format the results (add rank and suffix) and reorder them if needed
    best = [add_rank_and_suffix(best[i], i+1) for i in range(len(best))]
    worst = [add_rank_and_suffix(worst[i], total_applicable - i) for i in range(len(worst))]
    worst = sorted(worst, key=lambda x: x['rank'])
    # Create object to be used by Flask
    movies = [
        {'section': f'Best of {year_applicable}', 'movies': best, 'image': 'best.png'},
        {'section': f'Worst of {year_applicable}', 'movies': worst, 'image': 'worst.png'}
    ]

    tops = {}
    top_models = {
        'directors': {'role': 'director', 'nb_elements': 5},
        'actors': {'role': 'actor', 'nb_elements': 5},
        'actresses': {'role': 'actress', 'nb_elements': 5},
        'genres': {'role': 'genre', 'nb_elements': 5},
        'composers': {'role': 'composer', 'nb_elements': 3}
    }
    for top in top_models:
        values = Top.query \
            .filter_by(username=current_user.username) \
            .filter_by(role=top_models[top]['role']) \
            .order_by(Top.grade.desc(), Top.count.desc(), Top.rating.desc()) \
            .all()[:top_models[top]['nb_elements']]
        tops.update({top: values})

    return render_template('statistics.html', title='Statistics', counts=counts, tops=tops,
                           movies=movies, year=year_applicable)


def add_movie_grade(result):
    result = deepcopy(result)
    # Add the grade to result when seen already
    record = Record.query.with_entities(Record.grade) \
        .filter(Record.username == current_user.username) \
        .filter(Record.movie == result['movie']).first()
    if record:
        result.update({'grade': record[0]})
    return result


def add_movies_grade(results):
    results = deepcopy(results)
    # Add the grade to each result when seen already
    records = dict(Record.query.with_entities(Record.movie, Record.grade)
                   .filter(Record.username == current_user.username).all())
    for result in results:
        if records.get(result['movie']):
            result.update({'grade': records[result['movie']]})
    return results


@app.route('/', methods=['GET', 'POST'])
@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():

    if request.args.get('query'):
        query = request.args['query']
        nb_results = int(request.args.get('nb_results', 1))
        results, show_more_button = tmdb.search_movies(query, nb_results)
        results = add_movies_grade(results)
        scroll = int(request.args.get('scroll', 0))
        return render_template('search.html', query=query, results=results, scroll=scroll,
                               show_more_button=show_more_button, watchlist=get_watchlist_ids())

    else:
        return render_template('search.html', title='Search')


def get_watchlist_ids():
    # Query watchlist on DB
    watchlist = WatchlistItem.query.with_entities(WatchlistItem.movie) \
        .filter(WatchlistItem.username == current_user.username) \
        .all()
    return [item for item, in watchlist]


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
            tmdb_movie_id = int(get_post_result('add_to_watchlist'))
            # Add to watchlist on database
            item = WatchlistItem(insert_datetime=datetime.now(), username=current_user.username,
                                 **tmdb.movie(tmdb_movie_id))
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


@app.route('/movie/<movie_id>', methods=['GET', 'POST'])
@login_required
def movie(movie_id):

    # Get movie item
    movie_id = int(movie_id)
    movie = add_movie_grade(tmdb.movie(movie_id))

    if request.method == 'GET' and request.args.get('show_slider'):
        return render_template('movie.html', title='Movie', item=movie, mode='show_slider')

    if request.method == 'POST':

        if 'gradeRange' in request.form:

            # Get submitted grade
            grade = float(get_post_result('gradeRange'))

            if movie.get('grade'):
                action = 'updated'
                # Update the movie in the database
                Record.query \
                    .filter_by(username=current_user.username, movie=movie['movie']) \
                    .update({'grade': grade})
                db.session.commit()
            else:
                action = 'added'
                # Add the movie to the records database
                record = Record(username=current_user.username, movie=movie['movie'],
                                tmdb_id=movie['tmdb_id'], grade=grade)
                db.session.add(record)
                db.session.commit()

            # Remove from watchlist (if in it)
            remove_from_watchlist(movie['movie'])

            return render_template('movie.html', title='Movie', item=movie,
                                   mode='show_add_or_edit_confirmation', action=action)

        elif 'remove' in request.form:
            # Delete the movie from the database
            to_delete = Record.query.filter_by(username=current_user.username, movie=movie['movie']).all()
            for record in to_delete:
                db.session.delete(record)
            db.session.commit()
            return render_template('movie.html', title='Movie', item=movie,
                                   mode='show_remove_confirmation')

    return render_template('movie.html', title='Movie', item=movie, mode='show_buttons')
