import argparse
import logging
from getpass import getpass

from app import app, db
from app.models import User


LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Create argument parser
parser = argparse.ArgumentParser()
parser.add_argument('--username', '-u', required=True, help='Account whose password to set')
args = parser.parse_args()

with app.app_context():
    user = db.session.query(User).filter_by(username=args.username).one()

    # Prompt without echo, so that the password stays out of the screen, the shell history and the process list
    password = getpass('New password: ')
    assert password, 'Empty password'
    assert password == getpass('Repeat it: '), 'Passwords differ'

    user.set_password(password)
    db.session.commit()

    LOGGER.info(f'Password of {user.username} updated')
