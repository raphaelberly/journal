import re
from datetime import date, datetime, timedelta
from os import path

from flask import render_template, request, url_for, flash, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import func
from werkzeug.utils import redirect

from app import app
from app import db, login
from app.dbutils import upsert_title_metadata, async_execute
from app.forms import RegistrationForm
from app.models import Record, Title, Top, WatchlistItem, User
from lib.providers import Providers
from lib.tmdb import Tmdb, TitleConverter
from lib.tools import get_time_ago_string, get_time_spent_string

CURRENT_DIR = path.dirname(path.abspath(__file__))

tmdb = Tmdb()


def get_post_result(key):
    return request.form.to_dict()[key]


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(path.join(app.root_path, 'static'), 'images/favicon.ico', mimetype='image/vnd.microsoft.icon')


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

    payload = [(record.export(), title.export(current_user.language)) for record, title in query.all()]
    metadata = {
        'scroll': int(float(request.args.get('ref_scroll', 0))),
        'show_more_button': nb_recent > len(payload),
    }
    return render_template('recent.html', payload=payload, metadata=metadata)


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
    agg = db.session.query(func.coalesce(func.count(Title.title), 0), func.coalesce(func.sum(Title.runtime), 0),) \
        .select_from(Record).join(Title) \
        .filter(Record.user_id == current_user.id)
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
    start_date = db.session.query(func.min(Record.date)).filter(Record.user_id == current_user.id).scalar()
    overall_desc = f'since {start_date.strftime("%B, %Y")}' if start_date else 'overall'  # crashes if there's no "if"
    activity.update({'overall': {'values': dict(zip(activity_metrics, agg.first())), 'desc': overall_desc}})

    # Year applicable = this year if today > January 31st, else last year
    year_applicable = (date.today() - timedelta(days=31)).year
    if year_applicable == date.today().year:
        total_applicable = this_year[0]
    else:
        total_applicable = Record.query \
            .filter_by(user_id=current_user.id) \
            .filter(db.extract('year', Record.date) == year_applicable) \
            .count()
    # Query best and worst movies from applicable year
    query = db.session \
        .query(Record.date, Record.tmdb_id, Record.grade,
               Title.title, db.cast(db.extract('year', Title.release_date), db.Integer).label('year'), Title.genres) \
        .select_from(Record).join(Title) \
        .filter(Record.user_id == current_user.id) \
        .filter(db.extract('year', Record.date) == year_applicable)
    best = query.order_by(Record.grade.desc(), Record.insert_datetime_utc.desc()).limit(5).all()
    worst = query.order_by(Record.grade, Record.insert_datetime_utc.desc()).limit(5).all()
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
            .filter_by(user_id=current_user.id) \
            .filter_by(role=top_models[top]['role']) \
            .order_by(Top.grade.desc(), Top.count.desc()) \
            .all()[:top_models[top]['nb_elements']]
        tops.update({top: values})

    payload = {
        'activity': activity,
        'activity_metrics': activity_metrics,
        'tops': tops,
        'movies': movies,
        'year_applicable': year_applicable
    }
    metadata = {'scroll': int(float(request.args.get('ref_scroll', 0)))}
    return render_template('statistics.html', payload=payload, metadata=metadata)


def enrich_results(results):
    # Query (tmdb_id, grade, date) of results which were already graded by user
    records = Record.query.with_entities(Record.tmdb_id, Record.grade, Record.date) \
        .filter(Record.user_id == current_user.id)  \
        .filter(Record.tmdb_id.in_([result['id'] for result in results])).all()
    records = dict({_id: {'grade': _grade, 'date': _date} for _id, _grade, _date in records})
    # Query ids of movies in user's watchlist
    watchlist_ids = get_watchlist_ids()
    # Create output dict
    output = []
    for res in results:
        output.append({
            **TitleConverter.json_to_front(res, current_user.language),
            'grade': records.get(res['id'], {}).get('grade'),
            'date': records.get(res['id'], {}).get('date'),
            'in_watchlist': res['id'] in watchlist_ids,
        })
    return output


@app.route('/', methods=['GET', 'POST'])
@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():

    if not request.args.get('query'):
        return render_template('search.html', metadata={})

    if request.method == 'POST':
        if 'add_to_watchlist' in request.form:
            tmdb_id = int(get_post_result('add_to_watchlist'))
            add_to_watchlist(tmdb_id)
            flash('Movie added to watchlist')

    query = request.args['query']
    nb_results = int(request.args.get('nb_results', 3))
    result_ids = tmdb.search(query)
    payload = enrich_results(tmdb.get_bulk(result_ids[:nb_results]))
    metadata = {
        'query': query,
        'scroll': int(float(request.args.get('ref_scroll', 0))),
        'show_more_button': nb_results < len(result_ids)
    }
    return render_template('search.html', payload=payload, metadata=metadata)


def get_watchlist_ids():
    ids = WatchlistItem.query \
        .with_entities(WatchlistItem.tmdb_id) \
        .filter(WatchlistItem.user_id == current_user.id) \
        .all()
    return [_id for _id, in ids]


def add_to_watchlist(tmdb_id):
    title = tmdb.get(tmdb_id)
    upsert_title_metadata(title)
    providers = Providers().get_names(title['original_title'], tmdb_id)
    item = WatchlistItem(user_id=current_user.id, tmdb_id=tmdb_id, providers=providers)
    db.session.add(item)
    db.session.commit()


def remove_from_watchlist(tmdb_id):
    to_delete = WatchlistItem.query.filter_by(tmdb_id=tmdb_id, user_id=current_user.id).all()
    for record in to_delete:
        db.session.delete(record)
    db.session.commit()


@app.route('/watchlist', methods=['GET', 'POST'])
@login_required
def watchlist():

    if request.method == 'POST':
        if 'remove_from_watchlist' in request.form:
            tmdb_id = get_post_result('remove_from_watchlist')
            remove_from_watchlist(tmdb_id)
            flash('Movie removed from watchlist')

    query = db.session \
        .query(WatchlistItem, Title) \
        .select_from(WatchlistItem).join(Title) \
        .filter(WatchlistItem.user_id == current_user.id) \
        .order_by(WatchlistItem.insert_datetime_utc.desc())

    payload = [(watchlist_item.export(), title.export(current_user.language)) for watchlist_item, title in query.all()]
    metadata = {
        'scroll': int(float(request.args.get('ref_scroll', 0))),
        'filters': request.args.get('providers').split(',') if request.args.get('providers') else []
    }
    return render_template('watchlist.html', payload=payload, metadata=metadata)


def refresh_materialized_views():
    # Generate SQL request
    with open(path.join(CURRENT_DIR, 'queries/refresh_materialized_views.sql')) as f:
        sql = f.read()
    # Asynchronous execution of materialized views refresh
    async_execute(sql)


@app.route('/movie/<tmdb_id>', methods=['GET', 'POST'])
@login_required
def movie(tmdb_id):

    # Get movie item
    tmdb_id = int(tmdb_id)
    _title = tmdb.get(tmdb_id)
    title = enrich_results([_title])[0]

    # Get referrer if provided via GET params
    args = request.args.to_dict()
    referrer = args.pop('ref', 'search')
    scroll = int(float(args.pop('ref_scroll', 0)))

    if request.method == 'GET' and args.pop('show_slider', False):
        metadata = {
            'mode': 'show_slider',
            'referrer': referrer,
            'scroll': scroll,
            'grade_as_int': current_user.grade_as_int,
            'args': args
        }
        return render_template('movie.html', payload=title, metadata=metadata)

    if request.method == 'POST':

        if 'add_to_watchlist' in request.form:
            add_to_watchlist(tmdb_id)
            flash('Movie added to watchlist')

        elif 'remove' in request.form:
            # Delete the movie from the database
            to_delete = Record.query.filter_by(user_id=current_user.id, tmdb_id=tmdb_id).all()
            for record in to_delete:
                db.session.delete(record)
            db.session.commit()
            flash('Movie successfully removed')
            # Update title element
            title.pop('grade')
            title.pop('date')
            # Start statistics refresh
            refresh_materialized_views()

        elif 'gradeRange' in request.form:
            # Get submitted grade
            grade = float(get_post_result('gradeRange'))
            # If there is already a grade, then it's an update. Otherwise it's an addition
            if title.get('grade') is not None:
                action = 'updated'
                # Update the movie in the records table
                Record.query \
                    .filter_by(user_id=current_user.id, tmdb_id=tmdb_id) \
                    .update({'grade': grade, 'update_datetime_utc': datetime.utcnow()})
            else:
                action = 'added'
                # Add the movie to the titles table
                upsert_title_metadata(_title)
                # Add the movie to the records table
                record = Record(current_user.id, tmdb_id, grade)
                db.session.add(record)
                # Remove from watchlist (if in it)
                remove_from_watchlist(tmdb_id)
                # Update the title element
                title['date'] = datetime.utcnow().date()
            # Commit add/update changes
            db.session.commit()
            flash(f'Movie successfully {action}')
            # Update title element
            title['grade'] = grade
            # Start statistics refresh
            refresh_materialized_views()

    title['in_watchlist'] = tmdb_id in get_watchlist_ids()
    metadata = {
        'mode': 'show_edit_buttons' if title.get('grade') is not None else 'show_add_buttons',
        'referrer': referrer,
        'scroll': scroll,
        'args': args
    }
    return render_template('movie.html', payload=title, metadata=metadata)


@app.route('/people', methods=['GET', 'POST'])
@login_required
def people():

    if not request.args.get('query'):
        return render_template('people.html', metadata={})

    # Clean people query
    query = request.args['query']
    clean_query = "&".join([word for word in re.sub(r"[\W]", " ", query).split(" ") if len(word) > 0])
    # Generate SQL request
    with open(path.join(CURRENT_DIR, 'queries/people_search.sql')) as f:
        sql = f.read().format(query=clean_query, user_id=current_user.id)
    # Execute SQL request
    with db.engine.connect() as conn:
        response = conn.execute(sql)
    # Parse query response
    payload = [{k: v for k, v in zip(response._metadata.keys, row)} for row in response]
    metadata = {
        'query': query,
        'scroll': int(float(request.args.get('ref_scroll', 0))),
    }
    return render_template('people.html', payload=payload, metadata=metadata)
