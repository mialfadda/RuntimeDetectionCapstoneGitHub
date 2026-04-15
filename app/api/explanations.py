"""Explanation endpoints (Step 27). Reads from Explanation table + B2 mock."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app import limiter
from app.database.models import Explanation, URLSubmission, db
from app.interfaces.contracts import to_json
from app.interfaces.mocks import generate_explanation

explanations_bp = Blueprint("explanations", __name__)


@explanations_bp.get("/<int:scan_id>")
@jwt_required()
@limiter.limit("120/minute")
def get_explanation(scan_id: int):
    submission = db.session.get(URLSubmission, scan_id)
    if not submission:
        return jsonify({"error": "scan not found"}), 404
    stored = (
        Explanation.query.filter_by(predictionID=scan_id)
        .order_by(Explanation.creationTime.desc())
        .first()
    )
    if stored:
        return jsonify({
            "scan_id": scan_id,
            "method": stored.method,
            "summary_text": stored.rationale,
            "created_at": stored.creationTime.isoformat() if stored.creationTime else None,
        }), 200
    return jsonify(to_json(generate_explanation(scan_id, submission.url))), 200


@explanations_bp.post("/generate")
@jwt_required()
@limiter.limit("30/minute")
def generate():
    data = request.get_json(silent=True) or {}
    scan_id = data.get("scan_id")
    if not isinstance(scan_id, int):
        return jsonify({"error": "scan_id (int) is required"}), 400
    submission = db.session.get(URLSubmission, scan_id)
    if not submission:
        return jsonify({"error": "scan not found"}), 404
    result = generate_explanation(scan_id, submission.url)
    return jsonify(to_json(result)), 201
