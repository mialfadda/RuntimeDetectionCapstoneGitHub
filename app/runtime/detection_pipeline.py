"""Feature-dict construction for the ensemble.

The trained models expect a fixed 42-feature vector keyed by the names in
`feature_names.pkl` (all URL-derived). This module builds that dict from a
URL plus optional HTML/runtime evidence. Anything not in the model's feature
list is dropped at the alignment step inside each model wrapper, so HTML and
runtime fields are kept here for forward-compatibility when the models are
retrained on a richer feature set.
"""
import logging
from typing import Any, Optional

import requests

from app.runtime.html_extractor import extract_html_features
from app.runtime.runtime_monitor import extract_runtime_features
from app.runtime.url_extractor import extract_url_features

_log = logging.getLogger(__name__)


def fetch_page(url: str, timeout: float = 5.0) -> tuple[str, int]:
    """Best-effort HTML fetch. Returns ("", 0) on any failure."""
    try:
        if not url.startswith("http"):
            url = "http://" + url
        response = requests.get(
            url, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"}
        )
        return response.text, response.status_code
    except Exception as e:
        _log.debug("Page fetch failed for %s: %s", url, e)
        return "", 0


def build_feature_dict(
    url: str,
    html: Optional[str] = None,
    runtime_evidence: Optional[Any] = None,
) -> dict:
    """Build the canonical feature_dict consumed by the ensemble.

    Keys match the names in `feature_names.pkl` (everything else is ignored
    by the wrappers' alignment step, but kept here for retraining).
    """
    url_features = extract_url_features(url)
    html_features = extract_html_features(html or "")

    runtime_features: dict = {}
    if runtime_evidence is not None:
        runtime_features = extract_runtime_features(runtime_evidence)

    # The trained Decision Tree splits these punctuation features at
    # non-binary thresholds (e.g. `=` at 0.5/1.0/1.5/.../7.5, `%` up to
    # 20.5), so they were trained on COUNTS, not presence flags. main's
    # detection_pipeline.py mapped them to `1 if X in url else 0` which
    # silently produced wrong predictions; we use url.count(...) here.
    feature_dict = {
        # ── 42 features the model was trained on ──
        "url_len": url_features["url_length"],
        "@": url.count("@"),
        "?": url.count("?"),
        "-": url_features["num_hyphens"],          # already a count
        "=": url.count("="),
        ".": url_features["num_dots"],             # already a count
        "#": url.count("#"),
        "%": url.count("%"),
        "+": url.count("+"),
        "$": url.count("$"),
        "!": url.count("!"),
        "*": url.count("*"),
        ",": url.count(","),
        "//": url.count("//"),
        "digits": url_features["num_digits_in_url"],
        "letters": sum(c.isalpha() for c in url),
        "Shortining_Service": url_features["is_url_shortener"],
        "having_ip_address": url_features["has_ip_address"],
        "phish_urgency_words": url_features["has_suspicious_keywords"],
        "phish_security_words": url_features["has_suspicious_keywords"],
        "phish_brand_mentions": 0,
        "phish_brand_hijack": 0,
        "phish_multiple_subdomains": int(url_features["subdomain_count"] > 2),
        "phish_long_path": int(url_features["path_depth"] > 4),
        "phish_many_params": int("?" in url and url.count("=") > 2),
        "phish_suspicious_tld": 0,
        "phish_adv_exact_brand_match": 0,
        "phish_adv_brand_in_subdomain": 0,
        "phish_adv_brand_in_path": 0,
        "phish_adv_hyphen_count": url_features["num_hyphens"],
        "phish_adv_number_count": url_features["num_digits_in_url"],
        "phish_adv_suspicious_tld": 0,
        "phish_adv_long_domain": int(url_features["domain_length"] > 20),
        "phish_adv_many_subdomains": int(url_features["subdomain_count"] > 2),
        "phish_adv_encoded_chars": int("%" in url),
        "phish_adv_path_keywords": url_features["has_suspicious_keywords"],
        "phish_adv_has_redirect": html_features.get("has_redirect_meta", 0),
        "phish_adv_many_params": int(url.count("=") > 2),
        "path_has_hacked_terms": 0,
        "suspicious_extension": int(url.endswith((".exe", ".zip", ".php", ".js", ".bat"))),
        "path_underscore_count": url.count("_"),
        "is_gov_edu": int(url.endswith((".gov", ".edu"))),
        # ── Extra HTML / runtime fields (ignored by current model, kept for retraining) ──
        **{f"html_{k}": v for k, v in html_features.items()},
        **{f"rt_{k}": v for k, v in runtime_features.items()},
    }
    return feature_dict


_ensemble = None


def get_ensemble():
    """Lazy ensemble singleton — loads artifacts on first call only."""
    global _ensemble
    if _ensemble is None:
        from app.models.ensemble import EnsembleModel
        _ensemble = EnsembleModel()
    return _ensemble
