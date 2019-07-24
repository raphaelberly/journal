
from config.app import Config
from flask import Flask
from flask_login import LoginManager
from flask_cachebuster import CacheBuster
from flask_sqlalchemy import SQLAlchemy

# Initialise app
app = Flask(__name__)
app.config.from_object(Config)

# Initialise DB
db = SQLAlchemy(app)

# Initialise login manager
login = LoginManager(app)

# Create cache buster
cache_buster = CacheBuster(config={'extensions': ['.js', '.css', '.json'], 'hash_size': 5})
cache_buster.init_app(app)

from app import routes, models
