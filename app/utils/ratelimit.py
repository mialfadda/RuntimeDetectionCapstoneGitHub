"""Rate-limit violation logging (Step 12)."""
import logging

from flask import request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from app.database.models import RateLimitViolation, db

log = logging.getLogger(__name__)


def log_ratelimit_violation(exception) -> None:
    user_id = None
    try:
        verify_jwt_in_request(optional=True)
        ident = get_jwt_identity()
        user_id = int(ident) if ident else None
    except Exception:
        user_id = None
    try:
        row = RateLimitViolation(
            ipAddress=request.remote_addr,
            endpoint=request.path,
            userID=user_id,
        )
        db.session.add(row)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        log.warning("failed to log rate-limit violation: %s", e)
