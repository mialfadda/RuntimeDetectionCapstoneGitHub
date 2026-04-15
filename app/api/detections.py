"""User-facing scan history."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from app import limiter
from app.database.models import URLSubmission, db

detections_bp = Blueprint("detections", __name__)


@detections_bp.get("")
@jwt_required()
@limiter.limit("120/minute")
def list_detections():
    caller_id = int(get_jwt_identity())
    is_admin = get_jwt().get("role") == "admin"
    q = URLSubmission.query
    if not is_admin:
        q = q.filter_by(userID=caller_id)
    limit = min(int(request.args.get("limit", 50)), 200)
    rows = q.order_by(URLSubmission.creationDate.desc()).limit(limit).all()
    return jsonify({
        "detections": [
            {
                "scan_id": r.submissionID,
                "url": r.url,
                "status": r.status,
                "source": r.submissionSource,
                "created_at": r.creationDate.isoformat() if r.creationDate else None,
            }
            for r in rows
        ]
    })


@detections_bp.get("/<int:detection_id>")
@jwt_required()
@limiter.limit("120/minute")
def get_detection(detection_id: int):
    caller_id = int(get_jwt_identity())
    is_admin = get_jwt().get("role") == "admin"
    row = db.session.get(URLSubmission, detection_id)
    if not row or (not is_admin and row.userID != caller_id):
        return jsonify({"error": "not found"}), 404
    return jsonify({
        "scan_id": row.submissionID,
        "url": row.url,
        "status": row.status,
        "source": row.submissionSource,
        "created_at": row.creationDate.isoformat() if row.creationDate else None,
    })
