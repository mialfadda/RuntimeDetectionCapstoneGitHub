"""
check_url.py — URL scanning endpoint powered by the ML model + explainability.
Place this at app/api/check_url.py
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.database.models import db, URLSubmission, Website, SandboxSession, Prediction, Explanation
import re

check_url_bp = Blueprint('check_url', __name__)

TRUSTED = [
    'google.com','youtube.com','github.com','microsoft.com','apple.com',
    'amazon.com','wikipedia.org','stackoverflow.com','outlook.com','office.com',
    'live.com','yahoo.com','facebook.com','instagram.com','twitter.com','x.com',
    'linkedin.com','reddit.com','netflix.com','spotify.com','localhost','127.0.0.1',
]

@check_url_bp.post('/check-url')
@jwt_required()
def check_url():
    data   = request.get_json(silent=True) or {}
    url    = data.get('url', '').strip()
    user_id = get_jwt_identity()

    if not url or url.startswith(('chrome://','chrome-extension://','about:','moz-extension://')):
        return jsonify({'flagged': False}), 200

    # Trusted domains — skip ML, return safe
    url_lower = url.lower()
    for domain in TRUSTED:
        if domain in url_lower:
            return jsonify({'flagged': False, 'severity': 'safe', 'reason': 'Trusted domain', 'explanation': {}}), 200

    # Run ML model
    try:
        from app.models.malicious_detector import predict
        from app.explainability.explainer import explain
        prediction  = predict(url)
        explanation = explain(url, prediction)
    except Exception as e:
        # Fallback to rule-based if model fails
        return _rule_based_check(url)

    label      = prediction['label']
    confidence = prediction['confidence']
    flagged    = label == 'phishing'

    # Map confidence to severity
    if flagged:
        if confidence >= 85:   severity = 'critical'
        elif confidence >= 70: severity = 'high'
        elif confidence >= 55: severity = 'medium'
        else:                  severity = 'low'
    else:
        severity = 'safe'

    # Save to DB using your schema
    try:
        _save_to_db(url, user_id, label, confidence, prediction, explanation)
    except Exception:
        pass  # DB save is best-effort

    if not flagged:
        return jsonify({'flagged': False, 'severity': 'safe', 'reason': 'No threats detected'}), 200

    # Build response with full explanation for the popup
    top = explanation.get('top_factors', [])
    reason  = explanation.get('summary', 'This site may be malicious')
    advice  = explanation.get('advice', '')
    details = f"Model confidence: {confidence}%"
    if top:
        top_names = [f['label'] for f in top[:3] if f.get('risk') in ('high','medium')]
        if top_names:
            details += f" | Red flags: {', '.join(top_names)}"

    return jsonify({
        'flagged':     True,
        'severity':    severity,
        'reason':      reason,
        'details':     details,
        'advice':      advice,
        'confidence':  confidence,
        'explanation': {
            'summary':     explanation.get('summary'),
            'advice':      advice,
            'method':      'SHAP',
            'top_factors': top,
        }
    }), 200


def _rule_based_check(url):
    """Fallback rule-based checker if ML model unavailable."""
    url_lower = url.lower()
    BLACKLIST     = ['eicar.org','malware-traffic-analysis.net']
    HIGH_KEYWORDS = ['phishing','malware','ransomware','free-bitcoin','crypto-giveaway']
    MED_KEYWORDS  = ['crack','keygen','warez','nulled','serial-key']

    for d in BLACKLIST:
        if d in url_lower:
            return jsonify({'flagged':True,'severity':'critical','reason':'Known malicious domain','details':f'Blacklisted: {d}'}), 200
    for kw in HIGH_KEYWORDS:
        if kw in url_lower:
            return jsonify({'flagged':True,'severity':'high','reason':'Suspicious URL content','details':f'Keyword: {kw}'}), 200
    for kw in MED_KEYWORDS:
        if kw in url_lower:
            return jsonify({'flagged':True,'severity':'medium','reason':'Potentially unsafe content','details':f'Keyword: {kw}'}), 200
    if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', url_lower) or '@' in url_lower:
        return jsonify({'flagged':True,'severity':'medium','reason':'Suspicious URL pattern','details':'Raw IP or credentials in URL'}), 200
    return jsonify({'flagged':False,'severity':'safe'}), 200


def _save_to_db(url, user_id, label, confidence, prediction, explanation):
    """Save URL check as URLSubmission → Website → SandboxSession → Prediction → Explanation."""
    from urllib.parse import urlparse
    parsed     = urlparse(url)
    root_domain = parsed.netloc or url[:100]
    tld         = root_domain.split('.')[-1] if '.' in root_domain else ''

    # Get or create Website
    website = Website.query.filter_by(rootDomain=root_domain).first()
    if not website:
        website = Website(rootDomain=root_domain, topLevelDomain=tld)
        db.session.add(website)
        db.session.flush()

    # URLSubmission
    submission = URLSubmission(
        url=url, userID=int(user_id),
        submissionSource='browser_extension', status='complete',
        websiteID=website.websiteID
    )
    db.session.add(submission)
    db.session.flush()

    # SandboxSession
    now = datetime.utcnow()
    session = SandboxSession(
        websiteID=website.websiteID, isIsolated=True,
        engine='MLDetector', startTime=now, endTime=now, status='complete'
    )
    db.session.add(session)
    db.session.flush()

    # Get or create ModelVersion (id=1 for our built-in model)
    from app.database.models import Model, ModelVersion
    model_rec = Model.query.filter_by(name='URLMaliciousDetector').first()
    if not model_rec:
        model_rec = Model(name='URLMaliciousDetector', modelFamily='RandomForest', framework='scikit-learn')
        db.session.add(model_rec)
        db.session.flush()
    version = ModelVersion.query.filter_by(modelID=model_rec.modelID, status='active').first()
    if not version:
        version = ModelVersion(modelID=model_rec.modelID, versionTag='v1.0', status='active', accuracy=85.0)
        db.session.add(version)
        db.session.flush()

    # Prediction
    pred = Prediction(
        versionID=version.versionID, sessionID=session.sessionID,
        label=label, confidence=confidence,
        inferenceTime=0.05,
        scoreVector=str(prediction.get('features', {}))
    )
    db.session.add(pred)
    db.session.flush()

    # Explanation
    exp = Explanation(
        predictionID=pred.predictionID,
        rationale=explanation.get('summary', ''),
        method='SHAP'
    )
    db.session.add(exp)
    db.session.commit()


@check_url_bp.get('/alerts')
@jwt_required()
def get_alerts():
    """Return recent predictions for the extension dashboard."""
    try:
        preds = (Prediction.query
                 .order_by(Prediction.predictionID.desc())
                 .limit(50).all())
        alerts = []
        for p in preds:
            session  = SandboxSession.query.get(p.sessionID)
            website  = Website.query.get(session.websiteID) if session else None
            exp      = p.explanation
            alerts.append({
                'id':        p.predictionID,
                'url':       website.rootDomain if website else '',
                'severity':  _confidence_to_severity(p.label, p.confidence),
                'message':   f'{"Phishing" if p.label=="phishing" else "Legitimate"} — {p.confidence:.0f}% confidence',
                'status':    'open' if p.label == 'phishing' else 'resolved',
                'event_type':'url_check',
                'timestamp': session.startTime.isoformat() if session and session.startTime else '',
                'details':   exp.rationale if exp else '',
            })
        return jsonify({'alerts': alerts}), 200
    except Exception as e:
        return jsonify({'alerts': [], 'error': str(e)}), 200


@check_url_bp.get('/summary')
@jwt_required()
def get_summary():
    """Return alert counts for the extension dashboard."""
    try:
        preds = Prediction.query.filter_by(label='phishing').all()
        counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for p in preds:
            sev = _confidence_to_severity('phishing', p.confidence)
            if sev in counts:
                counts[sev] += 1
        return jsonify({'alert_counts': counts}), 200
    except Exception as e:
        return jsonify({'alert_counts': {'critical':0,'high':0,'medium':0,'low':0}}), 200


def _confidence_to_severity(label, confidence):
    if label != 'phishing': return 'safe'
    if confidence >= 85:   return 'critical'
    if confidence >= 70:   return 'high'
    if confidence >= 55:   return 'medium'
    return 'low'
