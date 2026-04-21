import os

class ProductionConfig:
    # ─── DATABASE ───────────────────────────────────────────
    # In production use PostgreSQL not SQLite
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL',
        'postgresql://postgres:password@db:5432/capstone')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_POOL_TIMEOUT = 30
    SQLALCHEMY_POOL_RECYCLE = 1800
    # Pool size 10 means 10 simultaneous DB connections
    # Pool recycle prevents stale connections after 30 mins

    # ─── SECURITY ───────────────────────────────────────────
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-in-production')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'change-this-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = 3600
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # ─── REDIS + CELERY ─────────────────────────────────────
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
    CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://redis:6379/0')

    # ─── RATE LIMITING ──────────────────────────────────────
    RATELIMIT_ENABLED = True
    RATE_LIMIT_PER_MINUTE = 60

    # ─── GENERAL ────────────────────────────────────────────
    DEBUG = False
    TESTING = False
    PRIMARY_MODEL_PATH = os.environ.get('PRIMARY_MODEL_PATH', 'models/')
    LOG_LEVEL = 'INFO'