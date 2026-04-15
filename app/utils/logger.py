import logging
import json
from datetime import datetime
from pythonjsonlogger import jsonlogger


# ─── SETUP LOGGER ───────────────────────────────────────────
def setup_logger(name, log_file='logs/app.log', level=logging.INFO):
    """
    Creates a JSON logger that writes to both file and console.

    Usage: logger = setup_logger('my_module')
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate logs
    if logger.handlers:
        return logger

    # JSON formatter — makes logs machine readable
    formatter = jsonlogger.JsonFormatter(
        fmt='%(asctime)s %(name)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler — saves logs to file
    import os
    os.makedirs('logs', exist_ok=True)
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    # Console handler — shows logs in terminal
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# ─── SPECIFIC LOGGERS ───────────────────────────────────────
# each module gets its own logger with its own log file

def get_api_logger():
    # logs all API requests and responses
    return setup_logger('api', 'logs/api.log')


def get_detection_logger():
    # logs all URL scan events and results
    return setup_logger('detection', 'logs/detection.log')


def get_model_logger():
    # logs model inference times and results
    return setup_logger('model', 'logs/model.log')


def get_error_logger():
    # logs all errors and exceptions
    return setup_logger('error', 'logs/error.log', level=logging.ERROR)


def get_user_logger():
    # logs all user actions
    return setup_logger('user', 'logs/user.log')


# ─── LOG EVENT HELPERS ──────────────────────────────────────
def log_api_request(method, endpoint, user_id=None, status_code=None):
    logger = get_api_logger()
    logger.info('api_request', extra={
        'method': method,
        'endpoint': endpoint,
        'user_id': user_id,
        'status_code': status_code,
        'timestamp': datetime.utcnow().isoformat()
    })


def log_detection_event(url, label, confidence, user_id=None):
    logger = get_detection_logger()
    logger.info('detection_event', extra={
        'url': url,
        'label': label,
        'confidence': confidence,
        'user_id': user_id,
        'timestamp': datetime.utcnow().isoformat()
    })


def log_model_inference(model_name, version, inference_time, label):
    logger = get_model_logger()
    logger.info('model_inference', extra={
        'model_name': model_name,
        'version': version,
        'inference_time_ms': inference_time,
        'label': label,
        'timestamp': datetime.utcnow().isoformat()
    })


def log_error(error_type, message, user_id=None, extra_data=None):
    logger = get_error_logger()
    logger.error('error_event', extra={
        'error_type': error_type,
        'message': message,
        'user_id': user_id,
        'extra_data': extra_data,
        'timestamp': datetime.utcnow().isoformat()
    })


def log_user_action(user_id, action, target=None):
    logger = get_user_logger()
    logger.info('user_action', extra={
        'user_id': user_id,
        'action': action,
        'target': target,
        'timestamp': datetime.utcnow().isoformat()
    })