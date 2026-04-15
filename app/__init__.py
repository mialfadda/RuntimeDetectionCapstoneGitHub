import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.database.models import db
from config.config import config_by_name

jwt = JWTManager()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute", "5000/hour"],
    storage_uri="memory://",
)
cors = CORS()


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)

    config_name = config_name or os.getenv("FLASK_ENV", "development")
    app.config.from_object(config_by_name[config_name])

    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, origins=app.config.get("CORS_ORIGINS", []))
    limiter.init_app(app)

    from app.api.auth import auth_bp, is_jti_revoked
    from app.api.scan import scan_bp
    from app.api.detections import detections_bp
    from app.api.dashboard import dashboard_bp
    from app.api.explanations import explanations_bp
    from app.api.admin import admin_bp
    from app.utils.ratelimit import log_ratelimit_violation
    from app.utils.security import register_security_headers

    @jwt.token_in_blocklist_loader
    def _blocklist_check(_jwt_header, jwt_payload):
        return is_jti_revoked(jwt_payload["jti"])

    @jwt.unauthorized_loader
    def _missing_token(reason):
        return jsonify({"error": "unauthorized", "reason": reason}), 401

    @jwt.invalid_token_loader
    def _invalid_token(reason):
        return jsonify({"error": "invalid_token", "reason": reason}), 401

    @jwt.expired_token_loader
    def _expired(_header, _payload):
        return jsonify({"error": "token_expired"}), 401

    @app.errorhandler(429)
    def _ratelimited(e):
        log_ratelimit_violation(e)
        return jsonify({"error": "rate_limited", "detail": str(e.description)}), 429

    register_security_headers(app)

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(scan_bp, url_prefix="/scan")
    app.register_blueprint(detections_bp, url_prefix="/detections")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(explanations_bp, url_prefix="/explanations")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    with app.app_context():
        db.create_all()

    return app
