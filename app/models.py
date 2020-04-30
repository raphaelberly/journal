from datetime import datetime
from typing import List, Optional

from flask_login import UserMixin
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.declarative import DeclarativeMeta
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login
from lib.tmdb import TitleConverter, CrewConverter


@login.user_loader
def load_user(id_):
    return User.query.get(id_)


def upsert(table_model: DeclarativeMeta, records: List[dict], exclude: Optional[List[str]] = None):
    # Get list of primary keys
    primary_keys = [key.name for key in inspect(table_model).primary_key]
    # Assemble upsert statement
    statement = insert(table_model).values(records)
    cols_to_update = {col.name: col for col in statement.excluded if (not col.primary_key and col.name not in exclude)}
    upsert_statement = statement.on_conflict_do_update(index_elements=primary_keys, set_=cols_to_update)
    # Execute statement
    db.session.execute(upsert_statement)


class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True)
    password_hash = db.Column(db.String(128))
    email = db.Column(db.String(256))
    grade_as_int = db.Column(db.Boolean)
    insert_datetime_utc = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = {"schema": "journal"}
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
    runtime = db.Column(db.Integer)
    revenue = db.Column(db.Integer)
    budget = db.Column(db.Integer)
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
    insert_datetime_utc = db.Column(db.DateTime, default=datetime.utcnow)
    update_datetime_utc = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = {"schema": "journal"}
    __tablename__ = "credits"

    def __repr__(self):
        return f'<Credit: person {self.cast_id} in title {self.tmdb_id}>'


def upsert_title_metadata(item):
    # Parse title metadata and upsert to database
    title = TitleConverter.json_to_table(item)
    upsert(Title, [{**title, 'update_datetime_utc': datetime.utcnow()}], ['insert_datetime_utc'])
    # Parse credits and persons metadata and upsert to database
    persons, credits = [], []
    for person, credit in CrewConverter.crew_generator(item):
        persons.append({**person, 'update_datetime_utc': datetime.utcnow()})
        credits.append({**credit, 'update_datetime_utc': datetime.utcnow()})
    upsert(Person, persons, ['insert_datetime_utc'])
    upsert(Credit, credits, ['insert_datetime_utc'])
    # Commit changes
    db.session.commit()


class WatchlistItem(db.Model):

    user_id = db.Column(db.String(32), db.ForeignKey(User.id), primary_key=True)
    tmdb_id = db.Column(db.Integer, db.ForeignKey(Title.id), primary_key=True)
    providers = db.Column(db.ARRAY(db.String(64)))
    insert_datetime_utc = db.Column(db.DateTime, default=datetime.utcnow)

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

    __table_args__ = {"schema": "journal"}
    __tablename__ = "tops"

    def __repr__(self):
        return '<Top {0}: {1}>'.format(self.role, self.name)
