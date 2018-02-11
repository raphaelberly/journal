
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired


class SearchForm(FlaskForm):

    input = StringField('Input', validators=[DataRequired()])
    button = SubmitField('Search')
