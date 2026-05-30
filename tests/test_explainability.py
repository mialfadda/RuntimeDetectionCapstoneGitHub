"""Explainability tests, ported from main's test_explainability.py.

The original test pulled a phishing row from `data/dataset.csv`. Here we
synthesize an analogous high-suspicion feature_dict and verify the SHAP /
LIME / LLM outputs have the contract-required shape. LLM is tested in
template-fallback mode (no `OPENAI_API_KEY`) so the suite runs offline.
"""
from __future__ import annotations

import os

import pytest


pytest.importorskip("shap")
pytest.importorskip("lime")


def _phishy_feature_dict() -> dict:
    return {
        "url_len": 142, "@": 1, "?": 1, "-": 9, "=": 1, ".": 6,
        "#": 0, "%": 1, "+": 0, "$": 0, "!": 0, "*": 0, ",": 0, "//": 1,
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


def test_shap_explanation_shape():
    from app.explainability.shap_explainer import SHAPExplainer
    exp = SHAPExplainer()
    result = exp.explain(_phishy_feature_dict())
    assert {"predicted_label", "predicted_class", "top_features",
            "pushing_malicious", "pushing_benign", "base_value"} <= set(result.keys())
    assert result["predicted_label"] in {"benign", "defacement", "phishing", "malware"}
    assert len(result["top_features"]) > 0
    for entry in result["top_features"]:
        assert "feature" in entry and "shap_value" in entry


def test_lime_explanation_shape():
    from app.explainability.lime_explainer import LIMEExplainer
    exp = LIMEExplainer()
    result = exp.explain(_phishy_feature_dict(), num_features=5)
    assert {"predicted_label", "predicted_class", "top_features",
            "pushing_malicious", "pushing_benign"} <= set(result.keys())
    assert result["predicted_label"] in {"benign", "defacement", "phishing", "malware"}
    assert len(result["top_features"]) > 0
    for entry in result["top_features"]:
        assert "feature" in entry and "weight" in entry


def test_llm_template_fallback(monkeypatch):
    """Without OPENAI_API_KEY the LLM explainer must still return a summary."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from app.explainability.llm_explainer import LLMExplainer
    exp = LLMExplainer()

    scan_stub = {"predicted_label": "phishing", "confidence": 0.74}
    shap_stub = {
        "predicted_label": "phishing",
        "top_features": [{"feature": "phish_urgency_words", "shap_value": 0.42}],
        "pushing_malicious": [{"feature": "phish_urgency_words", "shap_value": 0.42}],
        "pushing_benign": [],
    }
    result = exp.explain(url="http://br-icloud.com.br", scan_result=scan_stub, shap_result=shap_stub)

    assert result["predicted_label"] == "phishing"
    assert result["recommended_action"] in {"safe_to_visit", "avoid", "proceed_with_caution"}
    assert isinstance(result["explanation"], str) and len(result["explanation"]) > 0


def test_pipeline_adapter_returns_master_contract():
    """End-to-end: adapter takes a ScanRequest, returns the master ScanResult."""
    from app.interfaces.contracts import ScanRequest, RiskLevel, ThreatCategory
    from app.interfaces.pipeline import run_pipeline

    req = ScanRequest(url="http://google.com")
    result = run_pipeline(req)

    assert isinstance(result.risk_level, RiskLevel)
    assert isinstance(result.threat_category, ThreatCategory)
    assert 0.0 <= result.confidence <= 1.0
    assert result.inference_time_ms is not None
    assert result.inference_time_ms >= 0
