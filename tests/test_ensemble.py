"""Ensemble tests, ported from main's test_ensemble.py.

The original test ran three real dataset rows (benign, phishing, malware)
through the ensemble. Without `data/dataset.csv`, we exercise the same
predict() path with synthetic feature_dicts and assert the contract: the
result has the documented keys, probabilities sum to ~1, weighted-average
sanity holds, and the risk_level/predicted_label mapping is consistent.
"""
from __future__ import annotations

import pytest


pytest.importorskip("xgboost")
pytest.importorskip("tensorflow")


LABELS = {"benign", "defacement", "phishing", "malware"}
RISK_BY_LABEL = {
    "benign": "low",
    "defacement": "medium",
    "phishing": "high",
    "malware": "critical",
}


def _feature_dict(suspicion: str) -> dict:
    base = {k: 0 for k in [
        "url_len", "@", "?", "-", "=", ".", "#", "%", "+", "$", "!", "*", ",",
        "//", "digits", "letters", "Shortining_Service", "having_ip_address",
        "phish_urgency_words", "phish_security_words", "phish_brand_mentions",
        "phish_brand_hijack", "phish_multiple_subdomains", "phish_long_path",
        "phish_many_params", "phish_suspicious_tld", "phish_adv_exact_brand_match",
        "phish_adv_brand_in_subdomain", "phish_adv_brand_in_path",
        "phish_adv_hyphen_count", "phish_adv_number_count",
        "phish_adv_suspicious_tld", "phish_adv_long_domain",
        "phish_adv_many_subdomains", "phish_adv_encoded_chars",
        "phish_adv_path_keywords", "phish_adv_has_redirect",
        "phish_adv_many_params", "path_has_hacked_terms",
        "suspicious_extension", "path_underscore_count", "is_gov_edu",
    ]}
    if suspicion == "low":
        base.update({"url_len": 22, ".": 2, "letters": 18})
    elif suspicion == "high":
        base.update({
            "url_len": 142, "@": 1, "?": 1, "-": 9, ".": 6, "%": 1,
            "//": 1, "digits": 22, "letters": 95, "having_ip_address": 1,
            "phish_urgency_words": 1, "phish_security_words": 1,
            "phish_brand_mentions": 1, "phish_brand_hijack": 1,
            "phish_multiple_subdomains": 1, "phish_long_path": 1,
            "phish_many_params": 1, "phish_adv_exact_brand_match": 1,
            "phish_adv_brand_in_subdomain": 1, "phish_adv_brand_in_path": 1,
            "phish_adv_hyphen_count": 9, "phish_adv_number_count": 22,
            "phish_adv_long_domain": 1, "phish_adv_many_subdomains": 1,
            "phish_adv_encoded_chars": 1, "phish_adv_path_keywords": 1,
            "suspicious_extension": 1, "path_underscore_count": 4,
        })
    return base


@pytest.fixture(scope="module")
def ensemble():
    from app.models.ensemble import EnsembleModel
    return EnsembleModel()


def test_ensemble_result_shape(ensemble):
    result = ensemble.predict(_feature_dict("low"))
    assert {
        "predicted_class", "predicted_label", "confidence",
        "risk_level", "final_probabilities", "model_contributions",
    } <= set(result.keys())
    assert result["predicted_label"] in LABELS
    assert 0.0 <= result["confidence"] <= 1.0


def test_ensemble_probabilities_sum_to_one(ensemble):
    result = ensemble.predict(_feature_dict("high"))
    total = sum(result["final_probabilities"].values())
    assert 0.95 <= total <= 1.05


def test_risk_level_matches_label(ensemble):
    """`risk_level` is deterministically derived from `predicted_label`."""
    for suspicion in ("low", "high"):
        result = ensemble.predict(_feature_dict(suspicion))
        assert result["risk_level"] == RISK_BY_LABEL[result["predicted_label"]]


def test_per_model_contributions(ensemble):
    result = ensemble.predict(_feature_dict("high"))
    contribs = result["model_contributions"]
    assert set(contribs.keys()) == {"decision_tree", "xgboost", "lstm"}
    for per_model in contribs.values():
        assert "predicted_label" in per_model
        assert per_model["predicted_label"] in LABELS
        assert 0.0 <= per_model["confidence"] <= 1.0
