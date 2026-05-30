"""User-facing scan history."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from app import limiter
from app.database.models import Explanation, Prediction, URLSubmission, db

detections_bp = Blueprint("detections", __name__)


# Fallback when a row predates the 4-class persistence change and only
# has a risk_level stored. The four legitimate categories map cleanly,
# so this is only ever used for legacy/orphan rows.
_LEGACY_CATEGORY_BY_RISK = {
    "safe": "benign",
    "low": "benign",
    "medium": "phishing",
    "high": "phishing",
    "critical": "malware",
}


@detections_bp.get("")
@jwt_required()
@limiter.limit("120/minute")
def list_detections():
    caller_id = int(get_jwt_identity())
    is_admin = get_jwt().get("role") == "admin"
    limit = min(int(request.args.get("limit", 50)), 200)

    q = (
        db.session.query(URLSubmission, Prediction.label)
        .outerjoin(Explanation, Explanation.submission_id == URLSubmission.submissionID)
        .outerjoin(Prediction, Prediction.predictionID == Explanation.predictionID)
    )
    if not is_admin:
        q = q.filter(URLSubmission.userID == caller_id)
    rows = q.order_by(URLSubmission.creationDate.desc()).limit(limit).all()

    return jsonify({
        "detections": [
            {
                "scan_id": r.submissionID,
                "url": r.url,
                "status": r.status,
                "risk_level": r.risk_level,
                "threat_category": (
                    label
                    if label in {"benign", "defacement", "phishing", "malware"}
                    else _LEGACY_CATEGORY_BY_RISK.get((r.risk_level or "").lower(), "benign")
                ),
                "confidence": r.confidence,
                "source": r.submissionSource,
                "created_at": r.creationDate.isoformat() if r.creationDate else None,
            }
            for r, label in rows
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
