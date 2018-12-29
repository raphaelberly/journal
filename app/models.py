
from app import db
from datetime import datetime


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
    movie = db.Column(db.String(9), primary_key=True)
    title = db.Column(db.String(256))
    year = db.Column(db.Integer)
    genres = db.Column(db.String(256))
    directors = db.Column(db.ARRAY(db.String(256)))
    cast = db.Column(db.ARRAY(db.String(256)))
    image = db.Column(db.String(1024))

    __tablename__ = "watchlist"
    __table_args__ = {"schema": "journal"}

    def __repr__(self):
        return '<Watchlist item {0}: {1}>'.format(self.movie, self.title)


class Record(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    insert_datetime = db.Column(db.DateTime, nullable=True)
    movie = db.Column(db.String(9), db.ForeignKey(Title.movie))
    date = db.Column(db.Date, nullable=False)
    grade = db.Column(db.Float, nullable=False)

    title = db.relationship("Title", back_populates="record")

    __tablename__ = "records"
    __table_args__ = {"schema": "journal"}

    def __init__(self, movie, grade):

        self.insert_datetime = datetime.now()
        self.movie = movie
        self.date = datetime.now().date()
        self.grade = grade

    def __repr__(self):
        return '<Movie {}>'.format(self.movie)


class Top(db.Model):

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
