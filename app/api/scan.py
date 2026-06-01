"""POST /scan/analyze — primary detection endpoint (Step 22)."""
import json

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app import limiter
from app.database.models import Explanation, Prediction, URLSubmission, db
from app.database.persistence import persist_prediction
from app.interfaces.contracts import RuntimeEvidence, ScanRequest, to_json
from app.interfaces.mocks import run_pipeline
from app.utils.validators import ValidationError, reject_injection, validate_url

scan_bp = Blueprint("scan", __name__)


@scan_bp.post("/analyze")
@jwt_required()
@limiter.limit("60/minute;1000/hour")
def analyze():
    data = request.get_json(silent=True) or {}
    try:
        url = validate_url(reject_injection(data.get("url", ""), "url"))
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

    evidence_payload = data.get("runtime_evidence")
    evidence = RuntimeEvidence(**evidence_payload) if isinstance(evidence_payload, dict) else None

    user_id = int(get_jwt_identity())
    submission = URLSubmission(
        url=url, submissionSource=data.get("source", "extension"),
        status="pending", userID=user_id,
    )
    db.session.add(submission)
    db.session.flush()

    result = run_pipeline(ScanRequest(url=url, user_id=user_id, runtime_evidence=evidence))
    result.scan_id = submission.submissionID

    submission.status = "complete"
    submission.risk_level = result.risk_level.value
    submission.confidence = result.confidence

    prediction_id = persist_prediction(submission, result)

    contributions_text = ", ".join(
        f"{mc.model_name}={mc.score:.2f}" for mc in (result.model_contributions or [])
    ) or "no model contributions recorded"

    exp = Explanation(
        submission_id=submission.submissionID,
        predictionID=prediction_id,
        rationale=(
            f"URL '{url}' was analyzed by the ensemble model. "
            f"Risk level: {result.risk_level.value}. "
            f"Threat category: {result.threat_category.value}. "
            f"Confidence: {round(result.confidence * 100, 1)}%. "
            f"Per-model scores: {contributions_text}."
        ),
        method='SHAP',
    )
    db.session.add(exp)

    current_app.logger.info(
        "scan %s -> %s/%s (%.3f)",
        url, result.threat_category.value, result.risk_level.value, result.confidence,
    )
    db.session.commit()
    return jsonify(to_json(result)), 200


@scan_bp.post("/batch")
@jwt_required()
@limiter.limit("10/minute")
def batch_analyze():
    data = request.get_json(silent=True) or {}
    urls = data.get("urls") or []
    if not isinstance(urls, list) or not urls:
        return jsonify({"error": "urls must be a non-empty list"}), 400
    if len(urls) > 50:
        return jsonify({"error": "batch limit is 50"}), 400
    results = []
    user_id = int(get_jwt_identity())
    for raw in urls:
        try:
            url = validate_url(reject_injection(raw, "url"))
        except ValidationError as e:
            results.append({"url": raw, "error": str(e)})
            continue
        res = run_pipeline(ScanRequest(url=url, user_id=user_id))
        results.append(to_json(res))
    return jsonify({"results": results}), 200
