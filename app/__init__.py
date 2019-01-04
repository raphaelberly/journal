
from flask import Flask
from flask_login import LoginManager
from config.app import Config
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
login = LoginManager(app)

from app import routes, models
