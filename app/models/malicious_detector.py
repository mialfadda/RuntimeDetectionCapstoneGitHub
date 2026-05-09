"""
Malicious URL Detector — uses URL feature extraction + scikit-learn
Trains a RandomForest on startup if no saved model exists.
"""
import os, re, pickle, math
import numpy as np

MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'malicious_detector_v1.pkl')

# ── Feature extraction ────────────────────────────────────────────────────────
def extract_features(url: str) -> np.ndarray:
    url = url.lower().strip()
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc or ''
        path   = parsed.path or ''
    except Exception:
        domain, path = '', ''

    features = [
        len(url),                                          # 1. URL length
        url.count('.'),                                    # 2. dot count
        url.count('-'),                                    # 3. hyphen count
        url.count('@'),                                    # 4. @ symbol
        url.count('//'),                                   # 5. double slash
        int(bool(re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', url))),  # 6. IP address
        len(domain),                                       # 7. domain length
        domain.count('-'),                                 # 8. hyphens in domain
        domain.count('.'),                                 # 9. dots in domain
        len(path),                                         # 10. path length
        url.count('%'),                                    # 11. percent encoding
        url.count('='),                                    # 12. equals signs
        url.count('?'),                                    # 13. query strings
        url.count('&'),                                    # 14. ampersands
        int(any(kw in url for kw in ['login','signin','verify','secure','account','update','confirm','bank','paypal','ebay','amazon'])),  # 15. phishing keywords
        int(any(kw in url for kw in ['free','win','prize','click','download','install'])),  # 16. spam keywords
        int(url.startswith('https')),                      # 17. HTTPS
        _entropy(url),                                     # 18. URL entropy
        len(re.findall(r'[0-9]', url)) / max(len(url),1), # 19. digit ratio
        int(domain.endswith(('.xyz','.tk','.ml','.ga','.cf','.gq','.pw','.top','.click'))),  # 20. suspicious TLD
    ]
    return np.array(features, dtype=float)

def _entropy(s):
    if not s: return 0
    freq = {}
    for c in s: freq[c] = freq.get(c, 0) + 1
    return -sum((f/len(s)) * math.log2(f/len(s)) for f in freq.values())

FEATURE_NAMES = [
    'url_length','dot_count','hyphen_count','at_symbol','double_slash',
    'has_ip','domain_length','domain_hyphens','domain_dots','path_length',
    'percent_encoding','equals_signs','query_strings','ampersands',
    'phishing_keywords','spam_keywords','uses_https','url_entropy',
    'digit_ratio','suspicious_tld'
]

# ── Training data (known phishing + legitimate URLs) ─────────────────────────
TRAINING_DATA = [
    # (url, label)  1=malicious, 0=legitimate
    ('http://paypal-secure-login.tk/verify', 1),
    ('http://192.168.1.1/admin/login', 1),
    ('http://free-bitcoin-win.xyz/claim', 1),
    ('http://google.com-account-verify.ml/signin', 1),
    ('http://apple-id-suspended.ga/update', 1),
    ('http://secure-bankofamerica.click/login', 1),
    ('http://download-free-keygen.pw/crack', 1),
    ('http://phishing-test.com/steal@credentials', 1),
    ('http://malware-install.top/setup.exe', 1),
    ('http://win-prize-now.cf/claim?user=target', 1),
    ('http://amazon-security-alert.xyz/verify', 1),
    ('http://paypal.com-login.ml/account', 1),
    ('http://update-your-ebay.tk/signin', 1),
    ('http://microsoft-support-alert.gq/fix', 1),
    ('http://suspicious-redirect.xyz/go?to=steal', 1),
    ('http://fake-antivirus-download.pw/install', 1),
    ('http://bank-account-suspended.cf/reactivate', 1),
    ('http://free-iphone-winner.ga/claim', 1),
    ('http://login-verify-now.click/auth', 1),
    ('http://your-account-hacked.tk/restore', 1),
    ('https://google.com/search?q=python', 0),
    ('https://github.com/user/repo', 0),
    ('https://stackoverflow.com/questions/12345', 0),
    ('https://wikipedia.org/wiki/Python', 0),
    ('https://youtube.com/watch?v=abc123', 0),
    ('https://microsoft.com/en-us/windows', 0),
    ('https://apple.com/iphone', 0),
    ('https://amazon.com/dp/B08N5WRWNW', 0),
    ('https://twitter.com/user/status/123', 0),
    ('https://linkedin.com/in/username', 0),
    ('https://reddit.com/r/python/comments/abc', 0),
    ('https://netflix.com/browse', 0),
    ('https://spotify.com/playlist/abc123', 0),
    ('https://docs.python.org/3/library', 0),
    ('https://news.ycombinator.com/item?id=123', 0),
    ('https://medium.com/@user/article', 0),
    ('https://npmjs.com/package/express', 0),
    ('https://pypi.org/project/flask', 0),
    ('https://developer.mozilla.org/en-US/docs', 0),
    ('https://cloudflare.com/learning/ddos', 0),
]

def _train_model():
    from sklearn.ensemble import RandomForestClassifier
    X = np.array([extract_features(url) for url, _ in TRAINING_DATA])
    y = np.array([label for _, label in TRAINING_DATA])
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X, y)
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(clf, f)
    return clf

def _load_model():
    if os.path.exists(MODEL_PATH):
        with open(MODEL_PATH, 'rb') as f:
            return pickle.load(f)
    return _train_model()

_model = None

def get_model():
    global _model
    if _model is None:
        try:
            _model = _load_model()
        except Exception:
            _model = _train_model()
    return _model

def predict(url: str) -> dict:
    """
    Returns:
        {
            label: 'phishing' | 'legitimate',
            confidence: float (0-100),
            features: dict of feature name -> value,
            top_features: list of (feature_name, importance, value),
        }
    """
    model = get_model()
    features = extract_features(url)
    proba = model.predict_proba(features.reshape(1, -1))[0]
    malicious_prob = proba[1] if len(proba) > 1 else proba[0]
    label = 'phishing' if malicious_prob >= 0.5 else 'legitimate'
    confidence = round(float(malicious_prob if label == 'phishing' else 1 - malicious_prob) * 100, 1)

    feature_dict = dict(zip(FEATURE_NAMES, features))

    # Top contributing features
    importances = model.feature_importances_
    top = sorted(zip(FEATURE_NAMES, importances, features), key=lambda x: x[1], reverse=True)[:5]
    top_features = [{'name': n, 'importance': round(float(i)*100,1), 'value': round(float(v),3)} for n,i,v in top]

    return {
        'label': label,
        'confidence': confidence,
        'malicious_probability': round(float(malicious_prob)*100, 1),
        'features': {k: round(float(v),3) for k,v in feature_dict.items()},
        'top_features': top_features,
    }
