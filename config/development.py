import os

class DevelopmentConfig:
    # ─── DATABASE ───────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL',
        'sqlite:///capstone.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ─── SECURITY ───────────────────────────────────────────
    SECRET_KEY = 'dev-secret-key'
    JWT_SECRET_KEY = 'dev-jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = 3600
    SESSION_COOKIE_SECURE = False

    # ─── REDIS + CELERY ─────────────────────────────────────
    REDIS_URL = 'redis://localhost:6379/0'
    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

    # ─── RATE LIMITING ──────────────────────────────────────
    RATELIMIT_ENABLED = False
    RATE_LIMIT_PER_MINUTE = 100

    # ─── GENERAL ────────────────────────────────────────────
    DEBUG = True
    TESTING = False
    PRIMARY_MODEL_PATH = 'models/'
    LOG_LEVEL = 'DEBUG'