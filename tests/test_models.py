"""Per-model wrapper tests, ported from main's test_models.py.

The original tests on `origin/main` loaded a real phishing/benign row from
`data/dataset.csv` (which isn't shipped with this repo) to construct a
realistic feature_dict. We swap that for two synthetic feature_dicts that
exercise the same code path: a benign-shaped vector and a malicious-shaped
vector. The wrappers' alignment step trims to the canonical feature list,
so the shape of the output is what we assert on — not the exact label.
"""
from __future__ import annotations

import pytest


pytest.importorskip("xgboost")
pytest.importorskip("tensorflow")
pytest.importorskip("joblib")


LABELS = {"benign", "defacement", "phishing", "malware"}


def _benign_feature_dict() -> dict:
    return {
        "url_len": 22,
        "@": 0, "?": 0, "-": 0, "=": 0, ".": 2, "#": 0, "%": 0, "+": 0,
        "$": 0, "!": 0, "*": 0, ",": 0, "//": 0,
        "digits": 0, "letters": 18,
        "Shortining_Service": 0, "having_ip_address": 0,
        "phish_urgency_words": 0, "phish_security_words": 0,
        "phish_brand_mentions": 0, "phish_brand_hijack": 0,
        "phish_multiple_subdomains": 0, "phish_long_path": 0,
        "phish_many_params": 0, "phish_suspicious_tld": 0,
        "phish_adv_exact_brand_match": 0, "phish_adv_brand_in_subdomain": 0,
        "phish_adv_brand_in_path": 0, "phish_adv_hyphen_count": 0,
        "phish_adv_number_count": 0, "phish_adv_suspicious_tld": 0,
        "phish_adv_long_domain": 0, "phish_adv_many_subdomains": 0,
        "phish_adv_encoded_chars": 0, "phish_adv_path_keywords": 0,
        "phish_adv_has_redirect": 0, "phish_adv_many_params": 0,
        "path_has_hacked_terms": 0, "suspicious_extension": 0,
        "path_underscore_count": 0, "is_gov_edu": 0,
    }


def _malicious_feature_dict() -> dict:
    # High-signal phishing/malware features.
    return {
        "url_len": 142,
        "@": 1, "?": 1, "-": 9, "=": 1, ".": 6, "#": 0, "%": 1, "+": 0,
        "$": 0, "!": 0, "*": 0, ",": 0, "//": 1,
        "digits": 22, "letters": 95,
        "Shortining_Service": 0, "having_ip_address": 1,
        "phish_urgency_words": 1, "phish_security_words": 1,
        "phish_brand_mentions": 1, "phish_brand_hijack": 1,
        "phish_multiple_subdomains": 1, "phish_long_path": 1,
        "phish_many_params": 1, "phish_suspicious_tld": 1,
        "phish_adv_exact_brand_match": 1, "phish_adv_brand_in_subdomain": 1,
        "phish_adv_brand_in_path": 1, "phish_adv_hyphen_count": 9,
        "phish_adv_number_count": 22, "phish_adv_suspicious_tld": 1,
        "phish_adv_long_domain": 1, "phish_adv_many_subdomains": 1,
        "phish_adv_encoded_chars": 1, "phish_adv_path_keywords": 1,
        "phish_adv_has_redirect": 1, "phish_adv_many_params": 1,
        "path_has_hacked_terms": 1, "suspicious_extension": 1,
        "path_underscore_count": 4, "is_gov_edu": 0,
    }


def _assert_prediction_shape(result: dict):
    assert set(result.keys()) >= {
        "model", "predicted_class", "predicted_label",
        "confidence", "probabilities",
    }
    assert result["predicted_label"] in LABELS
    assert 0 <= result["predicted_class"] <= 3
    assert 0.0 <= result["confidence"] <= 1.0
    assert set(result["probabilities"].keys()) == LABELS
    total = sum(result["probabilities"].values())
    assert 0.95 <= total <= 1.05, f"probabilities should sum to ~1, got {total}"


def test_decision_tree_predicts():
    from app.models.decision_tree_model import DecisionTreeModel
    dt = DecisionTreeModel()
    _assert_prediction_shape(dt.predict(_benign_feature_dict()))
    _assert_prediction_shape(dt.predict(_malicious_feature_dict()))


def test_xgboost_predicts():
    from app.models.xgboost_model import XGBoostModel
    xgb = XGBoostModel()
    _assert_prediction_shape(xgb.predict(_benign_feature_dict()))
    _assert_prediction_shape(xgb.predict(_malicious_feature_dict()))


def test_lstm_predicts():
    from app.models.lstm_model import LSTMModel
    lstm = LSTMModel()
    _assert_prediction_shape(lstm.predict(_benign_feature_dict()))
    _assert_prediction_shape(lstm.predict(_malicious_feature_dict()))


def test_malicious_features_lean_non_benign():
    """A vector dialled to maximum suspicion should not look benign to
    the tree-based branches. LSTM is allowed to disagree because it
    operates on scaled features and is more sensitive to magnitudes."""
    from app.models.decision_tree_model import DecisionTreeModel
    from app.models.xgboost_model import XGBoostModel

    feats = _malicious_feature_dict()
    assert DecisionTreeModel().predict(feats)["predicted_label"] != "benign"
    assert XGBoostModel().predict(feats)["predicted_label"] != "benign"
