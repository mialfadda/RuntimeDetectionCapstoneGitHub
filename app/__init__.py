from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.database.models import db
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from app.api.websocket import socketio

limiter = Limiter(key_func=get_remote_address, default_limits=["1000/hour"])

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///capstone.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TESTING'] = False
    app.config['JWT_SECRET_KEY'] = 'dev-secret-key-change-in-production'
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600
    app.config['RATELIMIT_ENABLED'] = True
    app.config['REPORTS_DIR'] = 'reports'

    db.init_app(app)
    Migrate(app, db)
    JWTManager(app)
    socketio.init_app(app)
    limiter.init_app(app)

    with app.app_context():
        db.create_all()

    from app.api.health import health_bp
    app.register_blueprint(health_bp)

    from app.api.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    from app.api.scan import scan_bp
    app.register_blueprint(scan_bp, url_prefix='/api/scan')

    from app.api.detections import detections_bp
    app.register_blueprint(detections_bp, url_prefix='/api/detections')

    from app.api.explanations import explanations_bp
    app.register_blueprint(explanations_bp, url_prefix='/api/explanations')

    from app.api.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')

    # Keep check_url for backwards compat
    from app.api.check_url import check_url_bp
    app.register_blueprint(check_url_bp, url_prefix='/api')

    return app
