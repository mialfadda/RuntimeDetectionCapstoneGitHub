from flask import Blueprint, jsonify
from datetime import datetime
from app.database.models import db
from app.utils.logger import get_api_logger

logger = get_api_logger()
health_bp = Blueprint('health', __name__)


# ─── GET /health ────────────────────────────────────────────
@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Quick health check — is the app alive?
    Returns 200 if healthy, 503 if not.
    """
    logger.info('health_check', extra={'endpoint': '/health'})
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'RuntimeDetectionCapstone'
    }), 200


# ─── GET /health/detailed ───────────────────────────────────
@health_bp.route('/health/detailed', methods=['GET'])
def health_check_detailed():
    """
    Detailed health check — checks database and Redis connections.
    Returns status of each component.
    """
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'components': {}
    }
    overall_healthy = True

    # Check database
    try:
        db.session.execute(db.text('SELECT 1'))
        health_status['components']['database'] = {
            'status': 'healthy',
            'message': 'Database connection successful'
        }
    except Exception as e:
        overall_healthy = False
        health_status['components']['database'] = {
            'status': 'unhealthy',
            'message': str(e)
        }

    # Check Redis
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0, socket_connect_timeout=1, socket_timeout=1)
        r.ping()
        health_status['components']['redis'] = {
            'status': 'healthy',
            'message': 'Redis connection successful'
        }
    except Exception as e:
        overall_healthy = False
        health_status['components']['redis'] = {
            'status': 'unhealthy',
            'message': str(e)
        }

    # Check Celery
    try:
        from celery_app import celery
        celery.control.inspect(timeout=1).ping()
        health_status['components']['celery'] = {
            'status': 'healthy',
            'message': 'Celery workers available'
        }
    except Exception as e:
        health_status['components']['celery'] = {
            'status': 'unknown',
            'message': 'No Celery workers running'
        }

    # Set overall status
    if not overall_healthy:
        health_status['status'] = 'unhealthy'
        logger.error('health_check_failed', extra=health_status)
        return jsonify(health_status), 503

    logger.info('health_check_detailed', extra={'status': 'healthy'})
    return jsonify(health_status), 200


# ─── GET /metrics ───────────────────────────────────────────
@health_bp.route('/metrics', methods=['GET'])
def metrics():
    """
    Prometheus-compatible metrics endpoint.
    Returns system statistics in plain text format.
    """
    from app.database.models import User, URLSubmission, Prediction, Reports

    try:
        # Gather metrics from database
        total_users      = User.query.count()
        total_submissions = URLSubmission.query.count()
        pending_submissions = URLSubmission.query.filter_by(status='pending').count()
        total_predictions = Prediction.query.count()
        phishing_detected = Prediction.query.filter_by(label='phishing').count()
        total_reports    = Reports.query.count()

        # Format as Prometheus text format
        metrics_text = f"""# HELP total_users Total number of registered users
# TYPE total_users gauge
total_users {total_users}

# HELP total_submissions Total URL submissions
# TYPE total_submissions counter
total_submissions {total_submissions}

# HELP pending_submissions Pending URL submissions
# TYPE pending_submissions gauge
pending_submissions {pending_submissions}

# HELP total_predictions Total predictions made
# TYPE total_predictions counter
total_predictions {total_predictions}

# HELP phishing_detected Total phishing URLs detected
# TYPE phishing_detected counter
phishing_detected {phishing_detected}

# HELP total_reports Total reports generated
# TYPE total_reports counter
total_reports {total_reports}
"""
        return metrics_text, 200, {'Content-Type': 'text/plain'}

    except Exception as e:
        logger.error('metrics_error', extra={'error': str(e)})
        return jsonify({'error': str(e)}), 500