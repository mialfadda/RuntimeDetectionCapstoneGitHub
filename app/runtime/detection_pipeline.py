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

    Delegates the 42 model features to `app.runtime.features` (which is
    reverse-engineered to reproduce the CSV's pre-computed columns; see
    scripts/validate_features.py for per-column agreement). HTML and
    runtime evidence are passed through as `html_*` / `rt_*` keys for
    future retraining — the model wrappers' alignment step drops them
    today because they aren't in feature_names.pkl.
    """
    from app.runtime.features import extract_features_from_url

    html_features = extract_html_features(html or "")
    runtime_features: dict = {}
    if runtime_evidence is not None:
        runtime_features = extract_runtime_features(runtime_evidence)

    feature_dict = extract_features_from_url(url)
    # Carry HTML/runtime metadata for retraining; ignored by current model.
    feature_dict.update({f"html_{k}": v for k, v in html_features.items()})
    feature_dict.update({f"rt_{k}": v for k, v in runtime_features.items()})
    return feature_dict


_ensemble = None


def get_ensemble():
    """Lazy ensemble singleton — loads artifacts on first call only."""
    global _ensemble
    if _ensemble is None:
        from app.models.ensemble import EnsembleModel
        _ensemble = EnsembleModel()
    return _ensemble
