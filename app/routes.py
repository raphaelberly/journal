from copy import deepcopy
from datetime import date, datetime, timedelta
from flask import render_template, request, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import func
from werkzeug.utils import redirect

from app import app
from app import db, login
from app.forms import RegistrationForm
from app.models import Record, Title, Top, WatchlistItem, User
from lib.providers import Providers
from lib.tmdb import Tmdb
from lib.tools import get_time_ago_string, get_time_spent_string

tmdb = Tmdb()


def get_post_result(key):
    return request.form.to_dict()[key]


# Load functions to be used in Jinja into Context processor
@app.context_processor
def utility_processor():

    def format_date(dt):
        return get_time_ago_string(dt)

    def format_timespan(minutes):
        return get_time_spent_string(minutes)

    return dict(format_date=format_date, format_timespan=format_timespan)


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
            flash(f'Welcome, {user.username}!')
            return redirect(url_for('search'))

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():

    if current_user.is_authenticated:
        return redirect(url_for('search'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(form.username.data, form.password.data, form.email.data)
        db.session.add(user)
        db.session.commit()
        login_user(user, remember=True, duration=timedelta(days=90))
        flash(f'Welcome, {user.username}!')
        return redirect(url_for('search'))

    return render_template('signup.html', form=form)


@app.route('/logout')
def logout():
    logout_user()
    flash('You were successfully logged out')
    return redirect(url_for('login'))


@app.route('/recent', methods=['GET'])
@login_required
def recent():

    nb_recent = Record.query \
        .filter(Record.user_id == current_user.id) \
        .filter(Record.recent == True) \
        .count()

    query = db.session \
        .query(Record, Title) \
        .select_from(Record).join(Title) \
        .filter(Record.user_id == current_user.id) \
        .filter(Record.recent == True) \
        .order_by(Record.date.desc(), Record.insert_datetime_utc.desc())

    nb_results = int(request.args.get('nb_results', 20))
    query = query.limit(nb_results)

    payload = [(record.export(), title.export()) for record, title in query.all()]
    show_button = nb_recent > len(payload)
    scroll = int(float(request.args.get('ref_scroll', 0)))
    return render_template('recent.html', payload=payload, show_button=show_button, scroll=scroll)


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

    activity = {}
    activity_metrics = ['viewing activity', 'time spent']
    agg = db.session.query(
            func.coalesce(func.count(Record.movie), 0),
            func.coalesce(func.sum(Title.duration), 0),
        ) \
        .select_from(Record).join(Record.title) \
        .filter(Record.username == current_user.username)
    # This month
    this_month = agg \
        .filter(db.extract('year', Record.date) == db.extract('year', date.today())) \
        .filter(db.extract('month', Record.date) == db.extract('month', date.today())) \
        .first()
    activity.update({'month': {'values': dict(zip(activity_metrics, this_month)), 'desc': 'this month'}})
    # This year
    this_year = agg \
        .filter(db.extract('year', Record.date) == db.extract('year', date.today())) \
        .first()
    activity.update({'year': {'values': dict(zip(activity_metrics, this_year)), 'desc': 'this year'}})
    # Overall
    start_date = db.session.query(func.min(Record.date)).filter(Record.username == current_user.username).scalar()
    overall_desc = f'since {start_date.strftime("%B, %Y")}' if start_date else 'overall'  # crashes if there's no "if"
    activity.update({'overall': {'values': dict(zip(activity_metrics, agg.first())), 'desc': overall_desc}})

    # Year applicable = this year if today > January 31st, else last year
    year_applicable = (date.today() - timedelta(days=31)).year
    if year_applicable == date.today().year:
        total_applicable = this_year[0]
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
    best = query.order_by(Record.grade.desc(), Record.insert_datetime.desc()).limit(5).all()
    worst = query.order_by(Record.grade, Record.insert_datetime.desc()).limit(5).all()
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

    scroll = int(float(request.args.get('ref_scroll', 0)))
    return render_template('statistics.html', activity=activity, activity_metrics=activity_metrics, tops=tops,
                           movies=movies, year=year_applicable, scroll=scroll)


def enrich_results(results):
    results = deepcopy(results)
    # Add the grade to each result when seen already
    records = Record.query.with_entities(Record.movie, Record.grade, Record.date) \
        .filter(Record.username == current_user.username)  \
        .filter(Record.movie.in_([result['movie'] for result in results])).all()
    records = dict({_movie: {'grade': _grade, 'date': _date} for _movie, _grade, _date in records})
    for result in results:
        if records.get(result['movie']):
            result.update(records[result['movie']])
    return results


@app.route('/', methods=['GET', 'POST'])
@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():

    if not request.args.get('query'):
        return render_template('search.html')

    query = request.args['query']
    nb_results = int(request.args.get('nb_results', 3))
    result_ids = tmdb.search(query)
    show_more_button = nb_results < len(result_ids)
    results = enrich_results(tmdb.movies(result_ids[:nb_results]))
    scroll = int(float(request.args.get('ref_scroll', 0)))

    if request.method == 'POST':
        if 'add_to_watchlist' in request.form:
            add_to_watchlist()
            flash('Movie added to watchlist')

    return render_template('search.html', query=query, results=results, scroll=scroll,
                           show_more_button=show_more_button, watchlist=get_watchlist_ids())


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


def add_to_watchlist():
    tmdb_movie_id = int(get_post_result('add_to_watchlist'))
    tmdb_movie = tmdb.movie(tmdb_movie_id)
    providers = Providers().get_names(tmdb_movie['title'], tmdb_movie_id)
    item = WatchlistItem(insert_datetime=datetime.now(), username=current_user.username, providers=providers, **tmdb_movie)
    db.session.add(item)
    db.session.commit()


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
        if 'remove_from_watchlist' in request.form:
            movie_id = get_post_result('remove_from_watchlist')
            remove_from_watchlist(movie_id)
            flash('Movie removed from watchlist')

    watchlist_dict = get_watchlist()
    scroll = int(float(request.args.get('ref_scroll', 0)))
    providers = request.args.get('providers').split(',') if request.args.get('providers') else []
    return render_template('watchlist.html', watchlist=watchlist_dict, scroll=scroll, providers=providers)


@app.route('/movie/<movie_id>', methods=['GET', 'POST'])
@login_required
def movie(movie_id):

    # Get movie item
    movie_id = int(movie_id)
    movie = enrich_results([tmdb.movie(movie_id)])[0]

    # Get referrer if provided via GET params
    args = request.args.to_dict()
    referrer = args.pop('ref', 'search')
    scroll = int(float(args.pop('ref_scroll', 0)))

    if request.method == 'GET' and args.pop('show_slider', False):
        grade_as_int = User.query.filter_by(username=current_user.username).first().grade_as_int
        return render_template('movie.html', item=movie, mode='show_slider', referrer=referrer, scroll=scroll,
                               grade_as_int=grade_as_int, args=args)

    if request.method == 'POST':

        if 'add_to_watchlist' in request.form:
            add_to_watchlist()
            flash('Movie added to watchlist')

        if 'remove' in request.form:
            # Delete the movie from the database
            to_delete = Record.query.filter_by(username=current_user.username, movie=movie['movie']).all()
            for record in to_delete:
                db.session.delete(record)
            db.session.commit()
            flash('Movie successfully removed')
            # Update movie element
            movie.pop('grade')
            movie.pop('date')

        elif 'gradeRange' in request.form:
            # Get submitted grade
            grade = float(get_post_result('gradeRange'))
            # If there is already a grade, then it's an update. Otherwise it's an addition
            if movie.get('grade'):
                action = 'updated'
                # Update the movie in the database
                Record.query \
                    .filter_by(username=current_user.username, movie=movie['movie']) \
                    .update({'grade': grade})
            else:
                action = 'added'
                # Add the movie to the records database
                record = Record(current_user.username, movie['movie'], movie['tmdb_id'], grade)
                db.session.add(record)
                # Remove from watchlist (if in it)
                remove_from_watchlist(movie['movie'])
            # Commit add/update changes
            db.session.commit()
            flash(f'Movie successfully {action}')
            # Update movie element
            movie['grade'] = grade
            movie['date'] = Record.query.with_entities(Record.date) \
                .filter_by(username=current_user.username, movie=movie['movie']) \
                .first()[0]

    mode = 'show_add_buttons' if movie.get('grade') is None else 'show_edit_buttons'
    return render_template('movie.html', item=movie, mode=mode, referrer=referrer, scroll=scroll,
                           watchlist=get_watchlist_ids(), args=args)
