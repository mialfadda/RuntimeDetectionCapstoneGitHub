from datetime import datetime
from app.database.models import db, ActionLog
from app.utils.logger import log_user_action


# ─── ACTION LOG SERVICE ─────────────────────────────────────

def log_action(admin_id, action, target=None, export_type=None):
    """
    Records an admin action to the database.
    Central function used by all other log functions below.

    Usage: log_action(admin_id=1, action='login', target='admin_panel')
    """
    try:
        action_log = ActionLog(
            adminID=admin_id,
            action=action,
            target=target,
            exportType=export_type,
            creationDate=datetime.utcnow()
        )
        db.session.add(action_log)
        db.session.commit()

        # Also write to JSON log file
        log_user_action(
            user_id=admin_id,
            action=action,
            target=target
        )

        return action_log

    except Exception as e:
        db.session.rollback()
        raise e


# ─── AUTH EVENTS ────────────────────────────────────────────

def log_login(admin_id):
    """Call this when an admin logs in"""
    return log_action(
        admin_id=admin_id,
        action='login',
        target='admin_panel'
    )

def log_logout(admin_id):
    """Call this when an admin logs out"""
    return log_action(
        admin_id=admin_id,
        action='logout',
        target='admin_panel'
    )


# ─── URL SUBMISSION EVENTS ──────────────────────────────────

def log_url_submission(admin_id, url):
    """Call this when an admin records a URL submission"""
    return log_action(
        admin_id=admin_id,
        action='submit_url',
        target=url
    )


# ─── DECISION OVERRIDE EVENTS ───────────────────────────────

def log_override(admin_id, prediction_id):
    """Call this when an admin overrides a prediction"""
    return log_action(
        admin_id=admin_id,
        action='override',
        target=f'prediction_{prediction_id}'
    )


# ─── EXPORT EVENTS ──────────────────────────────────────────

def log_export(admin_id, export_type, target):
    """Call this when an admin exports a report"""
    return log_action(
        admin_id=admin_id,
        action='export',
        target=target,
        export_type=export_type
    )


# ─── DELETE EVENTS ──────────────────────────────────────────

def log_delete(admin_id, target):
    """Call this when an admin deletes something"""
    return log_action(
        admin_id=admin_id,
        action='delete',
        target=target
    )


# ─── QUERY HELPERS ──────────────────────────────────────────

def get_admin_logs(admin_id):
    """Get all logs for a specific admin"""
    return ActionLog.query.filter_by(adminID=admin_id)\
                         .order_by(ActionLog.creationDate.desc()).all()

def get_recent_logs(limit=50):
    """Get the most recent logs across all admins"""
    return ActionLog.query.order_by(ActionLog.creationDate.desc())\
                         .limit(limit).all()

def get_logs_by_action(action):
    """Get all logs of a specific action type"""
    return ActionLog.query.filter_by(action=action)\
                         .order_by(ActionLog.creationDate.desc()).all()