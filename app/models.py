from datetime import datetime

from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import insert
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login


@login.user_loader
def load_user(username):
    return User.query.get(username)


class User(UserMixin, db.Model):

    username = db.Column(db.String(30), primary_key=True)
    password_hash = db.Column(db.String(100))
    email = db.Column(db.String(256))
    grade_as_int = db.Column(db.Boolean)

    __tablename__ = "users"
    __table_args__ = {"schema": "journal"}

    def __repr__(self):
        return '<User: {1}>'.format(self.id, self.username)

    def __init__(self, username, password, email, grade_as_int=True):
        self.username = username
        self.password_hash = generate_password_hash(password)
        self.email = email
        self.grade_as_int = grade_as_int

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Title(db.Model):

    tmdb_id = db.Column(db.Integer, primary_key=True)
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
    update_datetime_utc = db.Column(db.DateTime)

    __tablename__ = "titles"
    __table_args__ = {"schema": "journal"}

    def __repr__(self):
        return f'<Title {self.tmdb_id}: {self.title}>'

    @classmethod
    def upsert(cls, title):
        value = title.__dict__.copy()
        value.pop('_sa_instance_state')
        value.update({'update_datetime_utc': datetime.utcnow()})
        statement = insert(cls).values(**value).on_conflict_do_update(constraint='titles_pkey', set_=value)
        db.session.execute(statement)


class WatchlistItem(db.Model):

    username = db.Column(db.String(20), db.ForeignKey(User.username), primary_key=True)
    tmdb_id = db.Column(db.Integer, db.ForeignKey(Title.tmdb_id), primary_key=True)
    providers = db.Column(db.ARRAY(db.String(64)))

    __tablename__ = "watchlist"
    __table_args__ = {"schema": "journal"}

    def __init__(self, username, tmdb_id, providers):

        self.username = username
        self.tmdb_id = tmdb_id
        self.providers = providers

    def __repr__(self):
        return f'<Watchlist item: movie {self.tmdb_id} for {self.username}>'


class Record(db.Model):

    username = db.Column(db.String(20), db.ForeignKey(User.username), primary_key=True)
    tmdb_id = db.Column(db.Integer, db.ForeignKey(Title.tmdb_id), primary_key=True)
    imdb_id = db.Column(db.String(9))
    grade = db.Column(db.Float)
    date = db.Column(db.Date)
    recent = db.Column(db.Boolean)

    __tablename__ = "records"
    __table_args__ = {"schema": "journal"}

    def __init__(self, username, tmdb_id, imdb_id, grade, date=None, recent=True):

        self.username = username
        self.tmdb_id = tmdb_id
        self.imdb_id = imdb_id
        self.grade = grade
        self.date = date or datetime.now().date()
        self.recent = recent

    def __repr__(self):
        return f'<Record: movie {self.tmdb_id} by {self.username}>'


class Top(db.Model):

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
    __table_args__ = {"schema": "journal"}

    def __repr__(self):
        return '<Top {0}: {1}>'.format(self.role, self.name)
