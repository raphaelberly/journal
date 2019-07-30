from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from app.models import User


class RegistrationForm(FlaskForm):

    username = StringField(
        label='Username',
        validators=[DataRequired(), Length(5, 35)],
        render_kw={'placeholder': 'Username'}
    )
    email = StringField(
        label='Email',
        validators=[DataRequired(), Email()],
        render_kw={'placeholder': 'Email'}
    )
    password = PasswordField(
        label='Password',
        validators=[DataRequired(), Length(5, 35)],
        render_kw={'placeholder': 'Password'}
    )
    password2 = PasswordField(
        label='Repeat password',
        validators=[DataRequired(), EqualTo('password')],
        render_kw={'placeholder': 'Repeat password'}
    )
    submit = SubmitField(
        label='Register'
    )

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('This username is already used. Please enter a new one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')
