from getpass import getpass
from werkzeug.security import generate_password_hash

print(generate_password_hash(getpass('Please enter your password: ')))
