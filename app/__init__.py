from flask import Flask
from app.database.models import db

def create_app():
    app = Flask(__name__)

    # Database config — creates a local file called capstone.db
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///capstone.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TESTING'] = False

    # Connect database to app
    db.init_app(app)

    # Create all tables
    with app.app_context():
        db.create_all()

    return app