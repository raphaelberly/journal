import re
import sys
import traceback
from datetime import date, datetime, timedelta
from os import path

from flask import render_template, request, url_for, flash, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import func
from werkzeug.utils import redirect

from app import app
from app import db, login
from app.converters import TitleConverter
from app.dbutils import upsert_title_metadata, async_execute_text, execute_text
from app.forms import RegistrationForm
from app.models import Record, Title, Top, WatchlistItem, User, Person, BlacklistItem
from app.titles import TitleCollector
from lib.overseerr import Overseerr
from lib.plex import Plex
from lib.tools import get_time_ago_string, get_time_spent_string

CURRENT_DIR = path.dirname(path.abspath(__file__))

title_collector = TitleCollector()
plex = Plex()
overseerr = Overseerr()


def intersect(a, b):
    return set(a) & set(b)


# Add zip support for jinja2
app.jinja_env.globals.update(zip=zip)
app.jinja_env.globals.update(intersect=intersect)


@app.errorhandler(Exception)
def handle_exceptions(e):
    flash('Wops, something went wrong', category='error')
    etype, value, tb = sys.exc_info()
    app.logger.error(str(traceback.print_exception(etype, value, tb)))
    return redirect(request.referrer or url_for('search'))


def get_post_result(key):
    return request.form.to_dict()[key]


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(path.join(app.root_path, 'static'), 'images/favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/error')
def error():
    raise Exception('A test exception was raised')


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
            flash(f'Welcome, {user.username}!', category='success')
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
        flash(f'Welcome, {user.username}!', category='success')
        return redirect(url_for('search'))

    return render_template('signup.html', form=form)


@app.route('/logout')
def logout():
    logout_user()
    flash('You were successfully logged out', category='success')
    return redirect(url_for('login'))


@app.route('/recent', methods=['GET'])
@login_required
def recent():

    nb_recent = Record.query \
        .filter(Record.user_id == current_user.id) \
        .filter(Record.include_in_recent == True) \
        .count()

    query = db.session \
        .query(Record, Title) \
        .select_from(Record).join(Title) \
        .filter(Record.user_id == current_user.id) \
        .filter(Record.include_in_recent == True) \
        .order_by(Record.date.desc(), Record.insert_datetime_utc.desc())

    nb_results = int(request.args.get('nb_results', 20))
    query = query.limit(nb_results)

    payload = [(record.export(), title.export(current_user.language)) for record, title in query.all()]
    show_more_button = nb_recent > len(payload)
    metadata = {
        'scroll_to': int(float(request.args.get('scroll_to', 0))),
        'show_more_button': show_more_button,
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
        .filter(Record.include_in_recent == True) \
        .first()
    activity.update({'month': {'values': dict(zip(activity_metrics, this_month)), 'desc': 'this month'}})
    # This year
    this_year = agg \
        .filter(db.extract('year', Record.date) == db.extract('year', date.today())) \
        .filter(Record.include_in_recent == True) \
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
        .filter(Record.include_in_recent == True) \
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
    return render_template('statistics.html', payload=payload, metadata={})


def enrich_results(results):
    # Query (tmdb_id, grade, date) of results which were already graded by user
    records = Record.query \
        .filter(Record.user_id == current_user.id)  \
        .filter(Record.tmdb_id.in_([result['id'] for result in results])).all()
    records = dict({record.tmdb_id: record.export() for record in records})
    # Query ids of movies in user's watchlist
    watchlist_ids = get_watchlist_ids()
    # Create output dict
    output = []
    for res in results:
        output.append({
            **TitleConverter.json_to_front(res, current_user.language),
            'grade': records.get(res['id'], {}).get('grade'),
            'date': records.get(res['id'], {}).get('date'),
            'include_in_recent': records.get(res['id'], {}).get('include_in_recent', True),  # default to True
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
            flash('Movie added to watchlist', category='success')
        if 'remove_from_watchlist' in request.form:
            tmdb_id = int(get_post_result('remove_from_watchlist'))
            remove_from_watchlist(tmdb_id)
            flash('Movie removed from watchlist', category='success')

    query = request.args['query']
    nb_results = int(request.args.get('nb_results', 3))
    result_ids = title_collector.tmdb.search(query)
    payload = enrich_results(title_collector.collect_bulk(result_ids[:nb_results]))
    metadata = {
        'query': query,
        'scroll_to': int(float(request.args.get('scroll_to', 0))),
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
    title = title_collector.collect(tmdb_id)
    upsert_title_metadata(title)
    providers = title_collector.tmdb.providers(tmdb_id)
    if tmdb_id in plex.library:
        providers.append('plex')
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
            flash('Movie removed from watchlist', category='success')
        if 'request_on_plex' in request.form:
            tmdb_id = int(get_post_result('request_on_plex'))
            overseerr.request_title(tmdb_id)

    query = db.session \
        .query(WatchlistItem, Title) \
        .select_from(WatchlistItem).join(Title) \
        .filter(WatchlistItem.user_id == current_user.id) \
        .order_by(WatchlistItem.insert_datetime_utc.desc())

    request_statuses = overseerr.request_statuses
    payload = [(watchlist_item.export(), title.export(current_user.language)) for watchlist_item, title in query.all()]
    # If the user has plex, the movie is not yet tagged as available on plex in the watchlist, but the user requested
    # it and the request was completed, then add "plex" to the providers
    if 'plex' in current_user.providers:
        for watchlist_item, _ in payload:
            if 'plex' not in watchlist_item['providers']:
                if request_statuses.get(watchlist_item['tmdb_id'], -1) == 2:
                    watchlist_item['providers'].append('plex')
    metadata = {
        'scroll_to': int(float(request.args.get('scroll_to', 0))),
        'filters': request.args.get('providers').split(',') if request.args.get('providers') else [],
        'providers': current_user.providers,
        'request_statuses': request_statuses,
    }
    return render_template('watchlist.html', payload=payload, metadata=metadata)


def refresh_materialized_views():
    # Generate SQL request
    with open(path.join(CURRENT_DIR, 'queries/refresh_materialized_views.sql')) as f:
        sql = f.read()
    # Asynchronous execution of materialized views refresh
    async_execute_text(sql)


@app.route('/movie/<tmdb_id>', methods=['GET', 'POST'])
@login_required
def movie(tmdb_id):

    # Get movie item
    tmdb_id = int(tmdb_id)
    _title = title_collector.collect(tmdb_id)
    title = enrich_results([_title])[0]

    metadata = {}

    if request.method == 'GET' and request.args.get('show_slider', False):
        metadata.update({
            'mode': 'show_slider',
            'grade_as_int': current_user.grade_as_int,
        })
        return render_template('movie.html', payload=title, metadata=metadata)

    if request.method == 'POST':

        if 'add_to_watchlist' in request.form:
            add_to_watchlist(tmdb_id)
            flash('Movie added to watchlist', category='success')
        if 'remove_from_watchlist' in request.form:
            remove_from_watchlist(tmdb_id)
            flash('Movie removed from watchlist', category='success')

        elif 'remove' in request.form:
            # Delete the movie from the database
            to_delete = Record.query.filter_by(user_id=current_user.id, tmdb_id=tmdb_id).all()
            for record in to_delete:
                db.session.delete(record)
            db.session.commit()
            flash('Movie successfully removed', category='success')
            # Update title element
            title.pop('grade')
            title.pop('date')
            # Start statistics refresh
            refresh_materialized_views()

        elif 'gradeRange' in request.form:
            # Get submitted grade
            grade = float(get_post_result('gradeRange'))
            include_in_recent = 'include_in_recent' in request.form
            # If there is already a grade, then it's an update. Otherwise it's an addition
            if title.get('grade') is not None:
                action = 'updated'
                # Update the movie in the records table
                Record.query \
                    .filter_by(user_id=current_user.id, tmdb_id=tmdb_id) \
                    .update({
                        'grade': grade, 'include_in_recent': include_in_recent, 'update_datetime_utc': datetime.utcnow()
                    })
            else:
                action = 'added'
                # Add the movie to the titles table
                upsert_title_metadata(_title)
                # Add the movie to the records table
                record = Record(current_user.id, tmdb_id, grade, include_in_recent=include_in_recent)
                db.session.add(record)
                # Remove from watchlist (if in it)
                remove_from_watchlist(tmdb_id)
                # Update the title element
                title['date'] = datetime.utcnow().date()
            # Commit add/update changes
            db.session.commit()
            flash(f'Movie successfully {action}', category='success')
            # Update title element
            title['grade'] = grade
            # Start statistics refresh
            refresh_materialized_views()
    # Prepare page and title metadata
    title['in_watchlist'] = tmdb_id in get_watchlist_ids()
    metadata.update({
        'mode': 'show_edit_buttons' if title.get('grade') is not None else 'show_add_buttons',
    })
    return render_template('movie.html', payload=title, metadata=metadata)


@app.route('/people', methods=['GET', 'POST'])
@login_required
def people():

    if not request.args.get('person_id') and not request.args.get('query'):
        # Return empty people search page
        return render_template('people.html', payload={}, metadata={})

    elif request.args.get('query'):
        metadata = {'query': request.args.get('query')}
        # Clean people query
        query = request.args.get('query')
        clean_query = "&".join([word for word in re.sub(r"[\W]", " ", query).split(" ") if len(word) > 0])
        # Generate SQL request
        with open(path.join(CURRENT_DIR, 'queries/people_search_by_name.sql')) as f:
            sql = f.read().format(query=clean_query, user_id=current_user.id)

    else:
        metadata = {'person_id': request.args.get('person_id')}
        # Generate SQL request
        with open(path.join(CURRENT_DIR, 'queries/people_search_by_id.sql')) as f:
            sql = f.read().format(person_id=request.args.get('person_id'), user_id=current_user.id)

    # Execute SQL request
    response = execute_text(sql)
    # Parse query response
    payload = {'titles': [], 'person': {'roles': {}}}
    for i, row in enumerate(response):
        if i == 0:
            person = Person.query.filter_by(id=row._mapping['person_id']).first()
            payload['person']['name'] = person.name
            if person.profile_path:
                payload['person']['image'] = 'https://image.tmdb.org/t/p/w92' + person.profile_path
        title = {k: v for k, v in zip(response._metadata.keys, row)}
        for role in title['roles']:
            payload['person']['roles'][role] = payload['person']['roles'].get(role, 0) + 1
        payload['titles'].append(title)

    return render_template('people.html', payload=payload, metadata=metadata)


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():

    available_providers = {
        'netflix': 'Netflix',
        'amazonprimevideo': 'Amazon Prime Video',
        'canal': 'Canal+',
        'disneyplus': 'Disney+',
        'mubi': 'Mubi',
        'universcine': 'Univers Ciné',
        'plex': 'Plex',
    }
    user_providers = {provider: provider in current_user.providers for provider in available_providers.keys()}

    if request.method == 'GET':
        decimal_grades = not current_user.grade_as_int
        original_titles_fr = current_user.language == 'fr'

    elif request.method == 'POST':
        modified = False
        # If decimal_grades preference was changed, change it in the db
        decimal_grades = 'decimal_grades' in request.form
        if decimal_grades == current_user.grade_as_int:
            current_user.grade_as_int = not decimal_grades
            modified = True
        # If original_titles_fr preference was changed, change it in the db
        original_titles_fr = 'original_titles_fr' in request.form
        if original_titles_fr != (current_user.language == 'fr'):
            current_user.language = 'fr' if original_titles_fr else 'en'
            modified = True
        # If the list of providers was changed, change it in the db
        submitted_providers = {provider: provider in request.form for provider in available_providers}
        if submitted_providers != user_providers:
            current_user.providers = [k for k, v in submitted_providers.items() if v]
            user_providers = submitted_providers
            modified = True
        # Apply changes if any
        if modified:
            current_user.update_datetime_utc = datetime.utcnow()
            db.session.commit()
            flash('Settings were successfully updated', category='success')
        else:
            flash('No settings were changed', category='error')

    payload = {
        'decimal_grades': decimal_grades,
        'original_titles_fr': original_titles_fr,
        'providers': user_providers,
        'provider_names': available_providers,
    }

    return render_template('settings.html', payload=payload, metadata={})


def enrich_titles(title_ids):
    # Fetch data on required titles, keep ID as key, so you can order them later
    titles = {title.id: title for title in Title.query.filter(Title.id.in_(title_ids)).all()}
    # Query ids of movies in user's watchlist
    watchlist_ids = get_watchlist_ids()
    # Create output dict
    output = []
    for title_id in title_ids:
        output.append({
            **titles[title_id].export(language=current_user.language),
            'in_watchlist': title_id in watchlist_ids,
        })
    return output


@app.route('/recos', methods=['GET', 'POST'])
@login_required
def recos():

    if request.method == 'POST':
        if 'add_to_watchlist' in request.form:
            tmdb_id = int(get_post_result('add_to_watchlist'))
            add_to_watchlist(tmdb_id)
            flash('Movie added to watchlist', category='success')
        if 'remove_from_watchlist' in request.form:
            tmdb_id = int(get_post_result('remove_from_watchlist'))
            remove_from_watchlist(tmdb_id)
            flash('Movie removed from watchlist', category='success')
        if 'blacklist' in request.form:
            tmdb_id = int(get_post_result('blacklist'))
            item = BlacklistItem(current_user.id, tmdb_id)
            db.session.add(item)
            db.session.commit()
            flash('Movie hidden from recos', category='success')

    # Generate SQL request
    with open(path.join(CURRENT_DIR, 'queries/recommended_movies.sql')) as f:
        sql = f.read().format(user_id=current_user.id)
    # Execute SQL request and parse response
    response = execute_text(sql)
    title_ids = [title_id for title_id, in response]

    # Check whether we need to display "More" button
    nb_results = int(request.args.get('nb_results', 5))
    show_more_button = len(title_ids) > nb_results

    # Prepare payload and metadata
    payload = {'titles': enrich_titles(title_ids)[:nb_results]}
    metadata = {
        'scroll_to': int(float(request.args.get('scroll_to', 0))),
        'show_more_button': show_more_button,
    }

    return render_template('recos.html', payload=payload, metadata=metadata)
