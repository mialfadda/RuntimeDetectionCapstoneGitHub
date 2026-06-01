"""Persist a finished scan into the rich Prediction/Explanation graph.

The /scan/analyze endpoint already writes the URLSubmission row (so it
can return a scan_id). To keep the 4-class label queryable later — for
the dashboard's threat-category breakdown — we also write a Prediction
row through the SandboxSession + ModelVersion chain the schema requires.

DB writes here are best-effort: a failure should not block the API
response, since the scan itself succeeded.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from urllib.parse import urlparse

from app.database.models import (
    Explanation, Model, ModelVersion, Prediction, SandboxSession,
    URLSubmission, Website, db,
)
from app.interfaces.contracts import ScanResult, ThreatCategory

_log = logging.getLogger(__name__)


_THREAT_TO_LABEL = {
    ThreatCategory.BENIGN: "benign",
    ThreatCategory.DEFACEMENT: "defacement",
    ThreatCategory.PHISHING: "phishing",
    ThreatCategory.MALWARE: "malware",
    ThreatCategory.SPAM: "phishing",      # nearest legal label
    ThreatCategory.UNKNOWN: "benign",     # nearest legal label
}


def _get_or_create_website(url: str) -> Website:
    parsed = urlparse(url)
    root_domain = (parsed.netloc or url)[:300]
    tld = root_domain.split(".")[-1] if "." in root_domain else ""
    website = Website.query.filter_by(rootDomain=root_domain).first()
    if not website:
        website = Website(rootDomain=root_domain, topLevelDomain=tld)
        db.session.add(website)
        db.session.flush()
    return website


def _get_or_create_model_version(scan_result: ScanResult) -> ModelVersion:
    name = "URLDetectionEnsemble"
    model_rec = Model.query.filter_by(name=name).first()
    if not model_rec:
        model_rec = Model(
            name=name,
            modelFamily="Ensemble(DT+XGB+LSTM)",
            framework="scikit-learn+xgboost+keras",
        )
        db.session.add(model_rec)
        db.session.flush()

    version = ModelVersion.query.filter_by(
        modelID=model_rec.modelID, status="active"
    ).first()
    if not version:
        version = ModelVersion(
            modelID=model_rec.modelID,
            versionTag="v1.0",
            status="active",
            accuracy=None,
        )
        db.session.add(version)
        db.session.flush()
    return version


def persist_prediction(submission: URLSubmission, scan_result: ScanResult) -> int | None:
    """Persist a Prediction row carrying the 4-class label. Returns its ID.

    Safe to call inside the scan request handler: any exception is caught,
    the partial transaction rolled back, and None returned so the caller
    can still respond 200 with the API contract intact.
    """
    try:
        website = _get_or_create_website(submission.url)
        submission.websiteID = website.websiteID
        db.session.flush()

        now = datetime.utcnow()
        session = SandboxSession(
            websiteID=website.websiteID,
            isIsolated=True,
            engine="EnsembleDetector",
            startTime=now,
            endTime=now,
            status="complete",
        )
        db.session.add(session)
        db.session.flush()

        version = _get_or_create_model_version(scan_result)

        label = _THREAT_TO_LABEL.get(scan_result.threat_category, "benign")
        confidence_pct = round(min(max(scan_result.confidence * 100, 0.0), 100.0), 2)

        score_vector = json.dumps({
            mc.model_name: {"score": mc.score, "confidence": mc.confidence}
            for mc in (scan_result.model_contributions or [])
        })

        pred = Prediction(
            versionID=version.versionID,
            sessionID=session.sessionID,
            label=label,
            confidence=confidence_pct,
            inferenceTime=(scan_result.inference_time_ms or 0.0) / 1000.0,
            scoreVector=score_vector,
        )
        db.session.add(pred)
        db.session.flush()
        return pred.predictionID
    except Exception as e:
        _log.warning("Prediction persistence failed for scan %s: %s",
                     getattr(submission, "submissionID", None), e)
        db.session.rollback()
        return None
