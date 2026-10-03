from flask_wtf import FlaskForm
from sqlalchemy import func
from wtforms import StringField, EmailField, PasswordField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, Length, Regexp
from app.models import User


def strip(value: str | None) -> str | None:
    # Drop the space the iPhone keyboard adds after a suggested word
    return value.strip() if value else value


class RegistrationForm(FlaskForm):

    # Keep the hints of signup.html, and the messages of auth.js, in line with these rules
    username = StringField(
        label='Username',
        filters=[strip],
        validators=[
            DataRequired('Required'),
            Length(3, 32, 'Must be 3 to 32 characters long'),
            # Letters may be accented. The pattern below is the same rule, for the browser to check as you type
            Regexp(r'^[\w.-]+$', message='Only letters, digits, dots, dashes and underscores'),
        ],
        render_kw={'placeholder': 'Username', 'autocomplete': 'username', 'pattern': r'[\p{L}\p{N}_.\-]+',
                   'autocapitalize': 'none', 'autocorrect': 'off', 'spellcheck': 'false'}
    )
    email = EmailField(
        label='Email',
        filters=[strip],
        validators=[DataRequired('Required'), Email(granular_message=True)],
        render_kw={'placeholder': 'Email', 'autocomplete': 'email'}
    )
    password = PasswordField(
        label='Password',
        validators=[DataRequired('Required'), Length(min=5, message='Must be at least 5 characters long')],
        render_kw={'placeholder': 'Password', 'autocomplete': 'new-password',
                   'autocapitalize': 'none', 'autocorrect': 'off', 'spellcheck': 'false'}
    )
    submit = SubmitField(
        label='Register'
    )

    def validate_username(self, username):
        user = User.query.filter(func.lower(User.username) == username.data.lower()).first()
        if user is not None:
            raise ValidationError('This username is already taken')

    def validate_email(self, email):
        user = User.query.filter(func.lower(User.email) == email.data.lower()).first()
        if user is not None:
            raise ValidationError('This email is already used by another account')
