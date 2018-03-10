
from app import db
from datetime import datetime


class Record(db.Model):

    insert_datetime = db.Column(db.DateTime, nullable=True)
    movie = db.Column(db.String(9), primary_key=True)
    date = db.Column(db.Date, nullable=False)
    grade = db.Column(db.Float, nullable=False)

    __tablename__ = "views"  # TO CLEAN
    __table_args__ = {"schema": "journal"}  # TO CLEAN

    def __init__(self, movie, grade):

        self.insert_datetime = datetime.now()
        self.movie = movie
        self.date = datetime.now().date()
        self.grade = grade

    def __repr__(self):
        return '<Movie {}>'.format(self.movie)
