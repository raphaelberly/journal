
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class SearchForm(FlaskForm):

    input = StringField('Input', validators=[DataRequired()])
    button = SubmitField('Search')


class MoreResultForm(FlaskForm):

    moreButton = SubmitField('More movies...')


class ResultsForm(FlaskForm):
    cancelButton = SubmitField('Cancel')
    backButton = SubmitField('Back to search')

