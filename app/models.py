from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login
from lib.tmdb import TitleConverter


@login.user_loader
def load_user(id_):
    return User.query.get(id_)


class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True)
    password_hash = db.Column(db.String(128))
    email = db.Column(db.String(256))
    grade_as_int = db.Column(db.Boolean)
    language = db.Column(db.String(4))
    insert_datetime_utc = db.Column(db.DateTime, default=datetime.utcnow)
    update_datetime_utc = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = {"schema": "journal"}
    __tablename__ = "users"

    def __init__(self, username, password, email, grade_as_int=True, language='fr'):
        self.username = username
        self.password_hash = generate_password_hash(password)
        self.email = email
        self.grade_as_int = grade_as_int
        self.language = language

    def __repr__(self):
        return f'<User {self.id}: {self.username}>'

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Title(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    imdb_id = db.Column(db.String(32))
    title = db.Column(db.String(1024))
    release_date = db.Column(db.Date)
    original_title = db.Column(db.String(1024))
    original_language = db.Column(db.String(32))
    directors = db.Column(db.ARRAY(db.String(256)))
    genres = db.Column(db.ARRAY(db.String(256)))
    top_cast = db.Column(db.ARRAY(db.String(256)))
    poster_path = db.Column(db.String(1024))
    runtime = db.Column(db.SmallInteger)
    revenue = db.Column(db.BigInteger)
    budget = db.Column(db.BigInteger)
    tagline = db.Column(db.String(1024))
    insert_datetime_utc = db.Column(db.DateTime, default=datetime.utcnow)
    update_datetime_utc = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = {"schema": "journal"}
    __tablename__ = "titles"

    def __repr__(self):
        return f'<Title {self.id}: {self.title}>'

    @classmethod
    def from_tmdb(cls, item: dict):
        return cls(**TitleConverter.json_to_table(item))

    def export(self, language='fr'):
        return TitleConverter.table_to_front(self.__dict__, language)


class Person(db.Model):

    id = db.Column(db.Integer, db.ForeignKey(User.id), primary_key=True)
    name = db.Column(db.String(128))
    gender = db.Column(db.Integer)
    insert_datetime_utc = db.Column(db.DateTime, default=datetime.utcnow)
    update_datetime_utc = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = {"schema": "journal"}
    __tablename__ = "persons"

    def __repr__(self):
        return f'<Person {self.id}: {self.name}>'


class Credit(db.Model):

    id = db.Column(db.String(128), primary_key=True)
    tmdb_id = db.Column(db.Integer, db.ForeignKey(Title.id))
    person_id = db.Column(db.Integer, db.ForeignKey(Person.id))
    role = db.Column(db.String(128))
    cast_rank = db.Column(db.SmallInteger, nullable=True)
    insert_datetime_utc = db.Column(db.DateTime, default=datetime.utcnow)
    update_datetime_utc = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = {"schema": "journal"}
    __tablename__ = "credits"

    def __repr__(self):
        return f'<Credit: person {self.cast_id} in title {self.tmdb_id}>'


class WatchlistItem(db.Model):

    user_id = db.Column(db.String(32), db.ForeignKey(User.id), primary_key=True)
    tmdb_id = db.Column(db.Integer, db.ForeignKey(Title.id), primary_key=True)
    providers = db.Column(db.ARRAY(db.String(64)))
    insert_datetime_utc = db.Column(db.DateTime, default=datetime.utcnow)
    update_datetime_utc = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = {"schema": "journal"}
    __tablename__ = "watchlist"

    def __init__(self, user_id, tmdb_id, providers):
        self.user_id = user_id
        self.tmdb_id = tmdb_id
        self.providers = providers

    def __repr__(self):
        return f'<Watchlist item: movie {self.tmdb_id} for user {self.user_id}>'

    def export(self):
        value = self.__dict__.copy()
        value.pop('_sa_instance_state')
        return value


class Record(db.Model):

    user_id = db.Column(db.String(32), db.ForeignKey(User.id), primary_key=True)
    tmdb_id = db.Column(db.Integer, db.ForeignKey(Title.id), primary_key=True)
    grade = db.Column(db.Float)
    date = db.Column(db.Date)
    recent = db.Column(db.Boolean)
    insert_datetime_utc = db.Column(db.DateTime, default=datetime.utcnow)
    update_datetime_utc = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = {"schema": "journal"}
    __tablename__ = "records"

    def __init__(self, user_id, tmdb_id, grade, date=None, recent=True):
        self.user_id = user_id
        self.tmdb_id = tmdb_id
        self.grade = grade
        self.date = date or datetime.now().date()
        self.recent = recent

    def __repr__(self):
        return f'<Record: user {self.user_id} watched movie {self.tmdb_id}>'

    def export(self):
        value = self.__dict__.copy()
        value.pop('_sa_instance_state')
        return value


class Top(db.Model):

    user_id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(128), primary_key=True)
    name = db.Column(db.String(256), primary_key=True)
    top_3_movies = db.Column(db.ARRAY(db.String(1024)))
    top_3_movies_year = db.Column(db.ARRAY(db.Integer))
    grade = db.Column(db.Float)
    count = db.Column(db.Integer)
    count_threshold = db.Column(db.Integer)

    __table_args__ = {"schema": "journal"}
    __tablename__ = "tops"

    def __repr__(self):
        return '<Top {0}: {1}>'.format(self.role, self.name)
