from datetime import datetime

from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import insert
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login


@login.user_loader
def load_user(id_):
    return User.query.get(id_)


class JournalModel:

    __table_args__ = {"schema": "journal"}

    def export(self):
        value = self.__dict__.copy()
        value.pop('_sa_instance_state')
        return value


class User(UserMixin, db.Model, JournalModel):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True)
    password_hash = db.Column(db.String(128))
    email = db.Column(db.String(256))
    grade_as_int = db.Column(db.Boolean)
    insert_datetime_utc = db.Column(db.DateTime)

    __tablename__ = "users"

    def __init__(self, username, password, email, grade_as_int=True):
        self.username = username
        self.password_hash = generate_password_hash(password)
        self.email = email
        self.grade_as_int = grade_as_int

    def __repr__(self):
        return f'<User {self.id}: {self.username}>'

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Title(db.Model, JournalModel):

    id = db.Column(db.Integer, primary_key=True)
    imdb_id = db.Column(db.String(32))
    title = db.Column(db.String(1024))
    release_date = db.Column(db.Date)
    original_title = db.Column(db.String(1024))
    original_language = db.Column(db.String(32))
    directors = db.Column(db.ARRAY(db.String(256)))
    genres = db.Column(db.ARRAY(db.String(256)))
    top_cast = db.Column(db.ARRAY(db.String(256)))
    poster_url = db.Column(db.String(1024))
    runtime = db.Column(db.Integer)
    revenue = db.Column(db.Integer)
    budget = db.Column(db.Integer)
    tagline = db.Column(db.String(1024))
    insert_datetime_utc = db.Column(db.DateTime)
    update_datetime_utc = db.Column(db.DateTime)

    __tablename__ = "titles"

    def __repr__(self):
        return f'<Title {self.id}: {self.title}>'

    @classmethod
    def from_tmdb(cls, item: dict):
        kwargs = {
            'id': item['id'],
            'imdb_id': item['imdb_id'],
            'title': item['title'],
            'release_date': datetime.strptime(item['release_date'], '%Y-%m-%d'),
            'original_title': item['original_title'],
            'original_language': item['original_language'],
            'directors': [item['name'] for item in item['credits'].get('crew', []) if item['job'] == 'Director'],
            'genres': [genre['name'] for genre in item.get('genres', [])],
            'top_cast': [item['name'] for item in item['credits'].get('cast', [])[:3]],
            'poster_url': item['poster_path'] if item.get('poster_path') else None,
            'runtime': item['runtime'],
            'revenue': item['revenue'],
            'budget': item['budget'],
            'tagline': item['tagline'],
        }
        return cls(**kwargs)

    def upsert(self):
        value = self.__dict__.copy()
        value.pop('_sa_instance_state')
        value.update({'update_datetime_utc': datetime.utcnow()})
        statement = insert(self.__class__).values(**value).on_conflict_do_update(constraint='titles_pkey', set_=value)
        db.session.execute(statement)

    def export(self, language='fr'):
        title = self.__dict__
        output = {
            'id': title['id'],
            'title': title['original_title'] if title['original_language'] == language else title['title'],
            'year': title['release_date'].year,
            'genres': title['genres'][:3],
            'cast': title['top_cast'],
            'directors': title['directors'],
            'duration': f'{title["runtime"] // 60}h {title["runtime"] % 60}min' if title.get('runtime') else None,
            'image': 'https://image.tmdb.org/t/p/w200' + title['poster_path'] if title.get('poster_path') else None,
        }
        return output


class WatchlistItem(db.Model, JournalModel):

    user_id = db.Column(db.String(32), db.ForeignKey(User.id), primary_key=True)
    tmdb_id = db.Column(db.Integer, db.ForeignKey(Title.id), primary_key=True)
    providers = db.Column(db.ARRAY(db.String(64)))
    insert_datetime_utc = db.Column(db.DateTime)

    __tablename__ = "watchlist"

    def __init__(self, user_id, tmdb_id, providers):
        self.user_id = user_id
        self.tmdb_id = tmdb_id
        self.providers = providers

    def __repr__(self):
        return f'<Watchlist item: movie {self.tmdb_id} for user {self.user_id}>'


class Record(db.Model, JournalModel):

    user_id = db.Column(db.String(32), db.ForeignKey(User.id), primary_key=True)
    tmdb_id = db.Column(db.Integer, db.ForeignKey(Title.id), primary_key=True)
    grade = db.Column(db.Float)
    date = db.Column(db.Date)
    recent = db.Column(db.Boolean)
    insert_datetime_utc = db.Column(db.DateTime)

    __tablename__ = "records"

    def __init__(self, user_id, tmdb_id, grade, date=None, recent=True):
        self.user_id = user_id
        self.tmdb_id = tmdb_id
        self.grade = grade
        self.date = date or datetime.now().date()
        self.recent = recent

    def __repr__(self):
        return f'<Record: user {self.user_id} watched movie {self.tmdb_id}>'


class Top(db.Model, JournalModel):

    username = db.Column(db.String(20), primary_key=True)
    id = db.Column(db.String(9), primary_key=True)  # For genres, the ID is the name
    role = db.Column(db.String(256), primary_key=True)
    name = db.Column(db.String(256))
    top_3_movies = db.Column(db.ARRAY(db.String(256)))
    top_3_movies_year = db.Column(db.ARRAY(db.Integer))
    grade = db.Column(db.Float)
    rating = db.Column(db.Float)
    count = db.Column(db.Integer)
    count_threshold = db.Column(db.Integer)

    __tablename__ = "tops"

    def __repr__(self):
        return '<Top {0}: {1}>'.format(self.role, self.name)
