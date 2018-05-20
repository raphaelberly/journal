
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from wtforms.fields.html5 import DecimalRangeField


class SearchForm(FlaskForm):

    input = StringField('Input', validators=[DataRequired()])
    button = SubmitField('Search')


class MoreResultForm(FlaskForm):

    moreButton = SubmitField('Find more')


class AddForm(FlaskForm):

    gradeRange = DecimalRangeField()
    addButton = SubmitField('Add movie')

class ResultsForm(FlaskForm):

    cancelButton = SubmitField('Cancel')

