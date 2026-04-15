"""Dashboard analytics (Step 28) + report endpoints (Step 30)."""
import os
from datetime import datetime, timedelta

from flask import Blueprint, current_app, jsonify, request, send_file
from flask_jwt_extended import jwt_required
from sqlalchemy import func

from app import limiter
from app.database.models import (
    Model as MlModel,
    ModelVersion,
    Prediction,
    Reports,
    URLSubmission,
    db,
)
from app.utils.auth import role_required

dashboard_bp = Blueprint("dashboard", __name__)


def _parse_date_range():
    end = request.args.get("end")
    start = request.args.get("start")
    end_dt = datetime.fromisoformat(end) if end else datetime.utcnow()
    start_dt = datetime.fromisoformat(start) if start else end_dt - timedelta(days=30)
    return start_dt, end_dt


@dashboard_bp.get("/metrics")
@jwt_required()
@limiter.limit("120/minute")
def metrics():
    start, end = _parse_date_range()
    total = (
        db.session.query(func.count(URLSubmission.submissionID))
        .filter(URLSubmission.creationDate.between(start, end))
        .scalar()
    )
    completed = (
        db.session.query(func.count(URLSubmission.submissionID))
        .filter(URLSubmission.creationDate.between(start, end))
        .filter(URLSubmission.status == "completed")
        .scalar()
    )
    return jsonify({
        "start": start.isoformat(),
        "end": end.isoformat(),
        "total_scans": total,
        "completed_scans": completed,
        "pending_scans": total - completed,
    })


@dashboard_bp.get("/threats")
@jwt_required()
@limiter.limit("120/minute")
def threats():
    start, end = _parse_date_range()
    severity = request.args.get("severity")
    q = db.session.query(Prediction.label, func.count(Prediction.predictionID)).group_by(
        Prediction.label
    )
    if severity:
        q = q.filter(Prediction.label == severity)
    breakdown = {label: count for label, count in q.all()}
    return jsonify({"start": start.isoformat(), "end": end.isoformat(), "breakdown": breakdown})


@dashboard_bp.get("/models")
@jwt_required()
@limiter.limit("60/minute")
def models():
    rows = (
        db.session.query(MlModel.modelID, MlModel.name, ModelVersion.versionTag, ModelVersion.accuracy, ModelVersion.status)
        .join(ModelVersion, ModelVersion.modelID == MlModel.modelID, isouter=True)
        .all()
    )
    return jsonify({
        "models": [
            {"model_id": r[0], "name": r[1], "version": r[2], "accuracy": r[3], "status": r[4]}
            for r in rows
        ]
    })


@dashboard_bp.get("/reports")
@jwt_required()
@limiter.limit("60/minute")
def list_reports():
    reports = Reports.query.order_by(Reports.generationTime.desc()).limit(100).all()
    return jsonify({
        "reports": [
            {
                "report_id": r.reportID,
                "prediction_id": r.predictionID,
                "threat_level": r.threatLevel,
                "status": r.status,
                "format": r.format,
                "generated_at": r.generationTime.isoformat() if r.generationTime else None,
            }
            for r in reports
        ]
    })


@dashboard_bp.get("/reports/<int:report_id>/download")
@jwt_required()
@limiter.limit("30/minute")
def download_report(report_id: int):
    report = db.session.get(Reports, report_id)
    if not report:
        return jsonify({"error": "report not found"}), 404
    reports_dir = current_app.config.get("REPORTS_DIR")
    fmt = (report.format or "pdf").lower()
    path = os.path.join(reports_dir, f"report_{report_id}.{fmt}")
    if not os.path.exists(path):
        # Placeholder until A2's report generator lands.
        return jsonify({"error": "report file not yet generated"}), 202
    return send_file(path, as_attachment=True)


@dashboard_bp.post("/reports/generate")
@jwt_required()
@role_required("admin", "user")
@limiter.limit("10/minute")
def generate_report():
    data = request.get_json(silent=True) or {}
    prediction_id = data.get("prediction_id")
    fmt = (data.get("format") or "pdf").lower()
    if fmt not in ("pdf", "csv"):
        return jsonify({"error": "format must be pdf or csv"}), 400
    if not isinstance(prediction_id, int):
        return jsonify({"error": "prediction_id (int) is required"}), 400
    report = Reports(
        predictionID=prediction_id,
        threatLevel=data.get("threat_level", "unknown"),
        status="queued",
        summary=data.get("summary"),
        format=fmt,
    )
    db.session.add(report)
    db.session.commit()
    # Real generation happens in A2's Celery task (Step 29).
    return jsonify({"report_id": report.reportID, "status": "queued"}), 202
