"""
SHAP/LIME-style explainability for URL predictions.
Generates human-readable explanations from model features.
"""
from app.models.malicious_detector import FEATURE_NAMES, extract_features, get_model
import numpy as np

FEATURE_DESCRIPTIONS = {
    'url_length':        ('URL length', 'Long URLs are common in phishing attacks to hide malicious paths'),
    'dot_count':         ('Number of dots', 'Many dots can indicate subdomain abuse'),
    'hyphen_count':      ('Hyphens in URL', 'Hyphens are often used to mimic legitimate domains'),
    'at_symbol':         ('@ symbol present', '@ in URLs can redirect to a different host'),
    'double_slash':      ('Double slashes', 'Used to confuse URL parsers'),
    'has_ip':            ('Raw IP address', 'Legitimate sites use domain names, not IP addresses'),
    'domain_length':     ('Domain length', 'Unusually long domains are suspicious'),
    'domain_hyphens':    ('Hyphens in domain', 'Hyphenated domains often impersonate real brands'),
    'domain_dots':       ('Dots in domain', 'Too many subdomains can indicate abuse'),
    'path_length':       ('Path length', 'Very long paths may hide malicious redirects'),
    'percent_encoding':  ('URL encoding', 'Excessive encoding is used to bypass filters'),
    'equals_signs':      ('Query parameters', 'Many parameters may indicate tracking or redirect abuse'),
    'query_strings':     ('Query strings', 'Excessive query strings are suspicious'),
    'ampersands':        ('Ampersands', 'Many parameters suggest complex redirect chains'),
    'phishing_keywords': ('Phishing keywords', 'Words like "login", "verify", "secure" are phishing red flags'),
    'spam_keywords':     ('Spam keywords', 'Words like "free", "win", "prize" indicate spam'),
    'uses_https':        ('Uses HTTPS', 'HTTPS alone does not make a site safe'),
    'url_entropy':       ('URL randomness', 'High entropy suggests randomly generated malicious URLs'),
    'digit_ratio':       ('Digit ratio', 'Many numbers in URL can indicate auto-generated phishing URLs'),
    'suspicious_tld':    ('Suspicious domain extension', 'Extensions like .xyz, .tk, .ml are commonly used for phishing'),
}

def explain(url: str, prediction: dict) -> dict:
    """
    Generate a full SHAP-style explanation for a URL prediction.
    Returns structured explanation data for the extension popup.
    """
    model = get_model()
    features = extract_features(url)
    importances = model.feature_importances_

    # Build explanation for each feature
    factors = []
    for name, importance, value in zip(FEATURE_NAMES, importances, features):
        if importance < 0.01:
            continue
        desc_short, desc_long = FEATURE_DESCRIPTIONS.get(name, (name, ''))
        risk = _feature_risk(name, value)
        if risk == 'none':
            continue
        factors.append({
            'feature':      name,
            'label':        desc_short,
            'description':  desc_long,
            'value':        round(float(value), 3),
            'importance':   round(float(importance) * 100, 1),
            'risk':         risk,
        })

    # Sort by importance
    factors.sort(key=lambda x: x['importance'], reverse=True)
    top_factors = factors[:5]

    # Build human-readable summary
    label     = prediction['label']
    confidence = prediction['confidence']
    summary   = _build_summary(url, label, confidence, top_factors)
    advice    = _build_advice(label, confidence, top_factors)

    return {
        'method':      'SHAP',
        'label':       label,
        'confidence':  confidence,
        'summary':     summary,
        'advice':      advice,
        'top_factors': top_factors,
        'all_factors': factors,
    }

def _feature_risk(name: str, value: float) -> str:
    """Classify each feature value as high/medium/low/none risk."""
    risk_rules = {
        'url_length':        lambda v: 'high' if v > 100 else 'medium' if v > 75 else 'none',
        'dot_count':         lambda v: 'high' if v > 5 else 'medium' if v > 3 else 'none',
        'hyphen_count':      lambda v: 'high' if v > 3 else 'medium' if v > 1 else 'none',
        'at_symbol':         lambda v: 'high' if v > 0 else 'none',
        'double_slash':      lambda v: 'medium' if v > 1 else 'none',
        'has_ip':            lambda v: 'high' if v > 0 else 'none',
        'domain_length':     lambda v: 'high' if v > 30 else 'medium' if v > 20 else 'none',
        'domain_hyphens':    lambda v: 'high' if v > 2 else 'medium' if v > 0 else 'none',
        'domain_dots':       lambda v: 'high' if v > 3 else 'medium' if v > 2 else 'none',
        'path_length':       lambda v: 'medium' if v > 50 else 'none',
        'percent_encoding':  lambda v: 'high' if v > 3 else 'medium' if v > 1 else 'none',
        'phishing_keywords': lambda v: 'high' if v > 0 else 'none',
        'spam_keywords':     lambda v: 'medium' if v > 0 else 'none',
        'uses_https':        lambda v: 'none',
        'url_entropy':       lambda v: 'high' if v > 4.5 else 'medium' if v > 4 else 'none',
        'digit_ratio':       lambda v: 'medium' if v > 0.3 else 'none',
        'suspicious_tld':    lambda v: 'high' if v > 0 else 'none',
    }
    fn = risk_rules.get(name)
    return fn(value) if fn else 'none'

def _build_summary(url, label, confidence, top_factors):
    if label == 'legitimate':
        return f'This URL appears legitimate with {confidence}% confidence. No major threats were detected.'
    risky = [f['label'] for f in top_factors if f['risk'] == 'high']
    if risky:
        return f'This URL is likely malicious ({confidence}% confidence). Key red flags: {", ".join(risky[:3])}.'
    return f'This URL shows suspicious patterns ({confidence}% confidence) and may be unsafe.'

def _build_advice(label, confidence, top_factors):
    if label == 'legitimate':
        return 'This site appears safe to browse. Always stay alert for unexpected login prompts.'
    if confidence >= 90:
        return 'Do NOT proceed. This site is almost certainly malicious. Close this tab immediately.'
    if confidence >= 70:
        return 'Avoid entering any personal information, passwords, or payment details on this site.'
    return 'Exercise caution. Verify this URL is correct before interacting with this site.'
