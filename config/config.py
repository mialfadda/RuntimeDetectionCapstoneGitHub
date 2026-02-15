import os
from datetime import timedelta


class Config:
    """Base configuration - shared by all environments"""

    # ============================================================
    # FLASK SETTINGS
    # ============================================================
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # ============================================================
    # DATABASE SETTINGS
    # ============================================================
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Set to True to see SQL queries in console

    # ============================================================
    # JWT AUTHENTICATION SETTINGS
    # ============================================================
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_ALGORITHM = 'HS256'

    # ============================================================
    # API RATE LIMITING (From your NFRs)
    # ============================================================
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = 'redis://localhost:6379'  # Redis for rate limiting

    # API Rate Limits (requests per time period)
    RATE_LIMIT_PER_MINUTE = 60  # 60 requests per minute per user
    RATE_LIMIT_PER_HOUR = 1000  # 1000 requests per hour per user
    RATE_LIMIT_PER_DAY = 10000  # 10000 requests per day per user

    # ============================================================
    # ML MODEL SETTINGS
    # ============================================================
    # Model file paths
    MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
    PRIMARY_MODEL_PATH = os.path.join(MODEL_DIR, 'malicious_detector_v1.pkl')
    BACKUP_MODEL_PATH = os.path.join(MODEL_DIR, 'malicious_detector_backup.pkl')

    # Model configuration
    MODEL_VERSION = '1.0.0'
    MODEL_CONFIDENCE_THRESHOLD = 0.7  # Minimum confidence to flag as malicious
    MODEL_INFERENCE_TIMEOUT = 5  # Seconds before timeout

    # ============================================================
    # CELERY (ASYNC TASKS) SETTINGS
    # ============================================================
    CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    # ============================================================
    # REPORT GENERATION SETTINGS
    # ============================================================
    REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'reports')
    MAX_REPORT_SIZE_MB = 50
    REPORT_RETENTION_DAYS = 30

    # ============================================================
    # LOGGING SETTINGS
    # ============================================================
    LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # ============================================================
    # SECURITY SETTINGS
    # ============================================================
    # CORS settings (for browser extension)
    CORS_ORIGINS = ['chrome-extension://*', 'http://localhost:3000']

    # Session settings
    SESSION_COOKIE_SECURE = False  # Set to True in production (HTTPS only)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # ============================================================
    # PERFORMANCE SETTINGS
    # ============================================================
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max request size

    # ============================================================
    # CLOUD SERVICE CREDENTIALS (if using cloud)
    # ============================================================
    # AWS Settings (if deploying to AWS)
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

    # Azure Settings (if deploying to Azure)
    AZURE_STORAGE_CONNECTION_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING', '')

    # Google Cloud Settings (if deploying to GCP)
    GCP_PROJECT_ID = os.getenv('GCP_PROJECT_ID', '')
    GCP_CREDENTIALS_PATH = os.getenv('GCP_CREDENTIALS_PATH', '')


class DevelopmentConfig(Config):
    """Development environment configuration"""

    DEBUG = True
    TESTING = False

    # Development database (SQLite)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///phishing_detection_dev.db'
    )

    # Show SQL queries in console (helpful for debugging)
    SQLALCHEMY_ECHO = True

    # Relaxed rate limits for development
    RATE_LIMIT_PER_MINUTE = 1000
    RATE_LIMIT_PER_HOUR = 10000

    # Development-specific settings
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production environment configuration"""

    DEBUG = False
    TESTING = False

    # Production database (PostgreSQL)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://user:password@localhost:5432/phishing_detection'
    )

    # Strict rate limits for production
    RATE_LIMIT_PER_MINUTE = 60
    RATE_LIMIT_PER_HOUR = 1000

    # Production security
    SESSION_COOKIE_SECURE = True  # HTTPS only

    # Production logging
    LOG_LEVEL = 'WARNING'


class TestingConfig(Config):
    """Testing environment configuration"""

    DEBUG = False
    TESTING = True

    # In-memory database for tests (fast, isolated)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

    # Disable rate limiting for tests
    RATELIMIT_ENABLED = False

    # Fast inference for tests
    MODEL_INFERENCE_TIMEOUT = 1

    # Testing-specific settings
    LOG_LEVEL = 'DEBUG'


# Configuration dictionary - used by app factory
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}