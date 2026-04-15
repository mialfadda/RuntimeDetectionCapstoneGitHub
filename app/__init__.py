from flask import Flask
from app.database.models import db
from flask_migrate import Migrate

def create_app():
    app = Flask(__name__)

    # Database config
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///capstone.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TESTING'] = False

    # Connect database to app
    db.init_app(app)

    # Connect migrate to app
    # this is what tracks all your database changes
    Migrate(app, db)

    return app