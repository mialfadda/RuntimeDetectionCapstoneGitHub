from flask import Flask
from app.database.models import db
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

def create_app():
    app = Flask(__name__)

    # Database config
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///capstone.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TESTING'] = False

    # JWT config
    app.config['JWT_SECRET_KEY'] = 'dev-secret-key-change-in-production'
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600

    # Connect database to app
    db.init_app(app)

    # Connect migrate to app
    Migrate(app, db)

    # Connect JWT to app
    JWTManager(app)

    # Register blueprints
    from app.api.health import health_bp
    app.register_blueprint(health_bp)

    return app