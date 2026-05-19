import os

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_socketio import SocketIO

limiter = Limiter(key_func=get_remote_address)


def create_app():
    app = Flask(__name__)

    # Postgres URIs from some providers start with "postgres://" but SQLAlchemy
    # 2.x only accepts "postgresql://" — rewrite it transparently.
    db_url = os.getenv('DATABASE_URL', 'sqlite:///capstone.db')
    if db_url.startswith('postgres://'):
        db_url = 'postgresql://' + db_url[len('postgres://'):]

    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', app.config['JWT_SECRET_KEY'])
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 3600
    app.config['REPORTS_DIR'] = 'reports'
    app.config['MODEL_DIR'] = 'models'
    app.config['MODEL_UPLOAD_SECRET'] = os.getenv('MODEL_UPLOAD_SECRET', 'dev-model-upload-secret')
    app.config['MODEL_UPLOAD_MAX_MB'] = 200
    app.config['MODEL_UPLOAD_ALLOWED_EXT'] = ('.pkl', '.pt', '.joblib', '.h5', '.onnx')

    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
    dashboard_url = os.getenv('DASHBOARD_URL', 'http://localhost:5174')
    CORS(app,
         origins=[
             frontend_url,
             dashboard_url,
             "http://localhost:5173",
             "http://localhost:5174",
             "http://localhost:3000",
             "chrome-extension://*",
         ],
         supports_credentials=True,
         allow_headers=["Authorization", "Content-Type"])

    from app.database.models import db
    from flask_migrate import Migrate
    db.init_app(app)
    Migrate(app, db)
    jwt = JWTManager(app)
    limiter.init_app(app)

    from app.api.auth import is_jti_revoked

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        return is_jti_revoked(jwt_payload["jti"])

    from app.api.websocket import socketio
    socketio.init_app(app)

    with app.app_context():
        from app.api.health import health_bp
        from app.api.auth import auth_bp
        from app.api.scan import scan_bp
        from app.api.detections import detections_bp
        from app.api.explanations import explanations_bp
        from app.api.dashboard import dashboard_bp
        from app.api.admin import admin_bp

        app.register_blueprint(health_bp)
        app.register_blueprint(auth_bp,         url_prefix="/auth")
        app.register_blueprint(scan_bp,         url_prefix="/scan")
        app.register_blueprint(detections_bp,   url_prefix="/detections")
        app.register_blueprint(explanations_bp, url_prefix="/explanations")
        app.register_blueprint(dashboard_bp,    url_prefix="/dashboard")
        app.register_blueprint(admin_bp,        url_prefix="/admin")

    return app
