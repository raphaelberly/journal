from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30))
    password_hash = db.Column(db.String(100))
    email = db.Column(db.String(256))

    __tablename__ = "users"
    __table_args__ = {"schema": "journal"}

    def __repr__(self):
        return '<User {0}: {1}>'.format(self.id, self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Title(db.Model):

    movie = db.Column(db.String(9), primary_key=True)
    title = db.Column(db.String(256))
    genres = db.Column(db.String(256))
    year = db.Column(db.Integer)
    type = db.Column(db.String(256))
    duration = db.Column(db.String(256))

    record = db.relationship("Record", uselist=False, back_populates="title")

    __tablename__ = "titles"
    __table_args__ = {"schema": "journal"}

    def __repr__(self):
        return '<Title {0}: {1}>'.format(self.movie, self.title)


class WatchlistItem(db.Model):

    insert_datetime = db.Column(db.DateTime())
    username = db.Column(db.String(20), primary_key=True)
    movie = db.Column(db.String(9), primary_key=True)
    tmdb_id = db.Column(db.Integer)
    title = db.Column(db.String(256))
    year = db.Column(db.Integer)
    genres = db.Column(db.ARRAY(db.String(256)))
    directors = db.Column(db.ARRAY(db.String(256)))
    cast = db.Column(db.ARRAY(db.String(256)))
    duration = db.Column(db.String(10))
    image = db.Column(db.String(1024))

    __tablename__ = "watchlist"
    __table_args__ = {"schema": "journal"}

    def __repr__(self):
        return '<Watchlist item {0}: {1}>'.format(self.movie, self.title)


class Record(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    insert_datetime = db.Column(db.DateTime, nullable=True)
    movie = db.Column(db.String(9), db.ForeignKey(Title.movie), nullable=False)
    tmdb_id = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False)
    grade = db.Column(db.Float, nullable=False)
    username = db.Column(db.String(20), nullable=False)
    recent = db.Column(db.Boolean, nullable=True)

    title = db.relationship("Title", back_populates="record")

    __tablename__ = "records"
    __table_args__ = {"schema": "journal"}

    def __init__(self, username, movie, tmdb_id, grade):

        self.username = username
        self.insert_datetime = datetime.now()
        self.movie = movie
        self.tmdb_id = tmdb_id
        self.date = datetime.now().date()
        self.grade = grade

    def __repr__(self):
        return '<Movie {}>'.format(self.movie)


class Top(db.Model):

    username = db.Column(db.String(20), primary_key=True)
    person = db.Column(db.String(9), primary_key=True)
    role = db.Column(db.String(256), primary_key=True)
    name = db.Column(db.String(256))
    top_3_movies = db.Column(db.ARRAY(db.String(256)))
    top_3_movies_year = db.Column(db.ARRAY(db.Integer))
    grade = db.Column(db.Float)
    rating = db.Column(db.Float)
    count = db.Column(db.Integer)

    __tablename__ = "tops"
    __table_args__ = {"schema": "journal"}

    def __repr__(self):
        return '<Top {0}: {1}>'.format(self.role, self.name)


class Genre(db.Model):

    username = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(256), primary_key=True)
    top_3_movies = db.Column(db.ARRAY(db.String(256)))
    top_3_movies_year = db.Column(db.ARRAY(db.Integer))
    grade = db.Column(db.Float)
    rating = db.Column(db.Float)
    count = db.Column(db.Integer)

    __tablename__ = "genres"
    __table_args__ = {"schema": "journal"}

    def __repr__(self):
        return '<Genre: {0}>'.format(self.name)
