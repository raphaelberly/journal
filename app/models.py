
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

    __tablename__ = "titles"  # TO CLEAN
    __table_args__ = {"schema": "journal"}  # TO CLEAN

    def __repr__(self):
        return '<Title {0}: {1}>'.format(self.movie, self.title)


class Record(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    insert_datetime = db.Column(db.DateTime, nullable=True)
    movie = db.Column(db.String(9), db.ForeignKey(Title.movie))
    date = db.Column(db.Date, nullable=False)
    grade = db.Column(db.Float, nullable=False)

    title = db.relationship("Title", back_populates="record")

    __tablename__ = "views"  # TO CLEAN
    __table_args__ = {"schema": "journal"}  # TO CLEAN

    def __init__(self, movie, grade):

        self.insert_datetime = datetime.now()
        self.movie = movie
        self.date = datetime.now().date()
        self.grade = grade

    def __repr__(self):
        return '<Movie {}>'.format(self.movie)
