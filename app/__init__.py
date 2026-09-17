from flask import Flask
from flask_cachebuster import CacheBuster
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

from config.app import Config

# Initialise app
app = Flask(__name__)
app.config.from_object(Config)

# Initialise DB
db = SQLAlchemy()
db.init_app(app)
app.app_context().push()

# Initialise login manager
login = LoginManager()
login.init_app(app)

# Protect every POST against CSRF. Tokens last as long as the session rather than the
# default hour: pages stay open for days in the standalone web-app
app.config['WTF_CSRF_TIME_LIMIT'] = None
csrf = CSRFProtect()
csrf.init_app(app)

# Create cache buster
cache_buster = CacheBuster(config={'extensions': ['.js', '.css', '.json'], 'hash_size': 5})
cache_buster.init_app(app)

from app import routes, models
