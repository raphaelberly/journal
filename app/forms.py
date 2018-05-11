
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from wtforms.fields.html5 import DecimalRangeField


class SearchForm(FlaskForm):

    input = StringField('Input', validators=[DataRequired()])
    button = SubmitField('Search')


class MoreResultForm(FlaskForm):

    moreButton = SubmitField('More results...')


class AddForm(FlaskForm):

    gradeRange = DecimalRangeField()
    addButton = SubmitField('Add Movie')


class ResultsForm(FlaskForm):

    cancelButton = SubmitField('Cancel')

