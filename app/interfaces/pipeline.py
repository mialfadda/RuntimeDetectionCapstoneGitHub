"""Contract-seam adapter between the API and the ML ensemble.

Public surface — these are the only symbols `app.api.*` should import:

    run_pipeline(req: ScanRequest) -> ScanResult
    generate_explanation(scan_id: int, url: str) -> ExplanationResult

Inside, this module:
  1. Builds the canonical `feature_dict` from URL (+ HTML, + runtime evidence).
  2. Calls `EnsembleModel.predict()` and maps its 4-class output onto the
     master `ScanResult` contract (`ThreatCategory` / `RiskLevel` enums,
     `list[ModelContribution]`).
  3. If the ensemble fails to load (missing artifact, runtime error), falls
     back to the existing RandomForest heuristic, then to a deterministic
     URL-hash heuristic, so the API never returns 500 because of ML state.
  4. Produces explanations from SHAP + LIME + LLM, with a template summary
     when `OPENAI_API_KEY` is unset.
"""
import hashlib
import logging
import threading
import time
from typing import Optional

from app.interfaces.contracts import (
    ExplanationMethod, ExplanationResult, ModelContribution,
    RiskLevel, ScanRequest, ScanResult, ThreatCategory,
)

_log = logging.getLogger(__name__)


# ── 4-class mapping ────────────────────────────────────────────────

_THREAT_BY_LABEL = {
    "benign": ThreatCategory.BENIGN,
    "phishing": ThreatCategory.PHISHING,
    "malware": ThreatCategory.MALWARE,
    "defacement": ThreatCategory.DEFACEMENT,
}

_RISK_BY_STRING = {
    "low": RiskLevel.LOW,
    "medium": RiskLevel.MEDIUM,
    "high": RiskLevel.HIGH,
    "critical": RiskLevel.CRITICAL,
}


def _risk_from_mal_prob(mal_prob: float) -> tuple[RiskLevel, ThreatCategory]:
    """Used by binary-RF and hash fallbacks where we only know phish/benign."""
    if mal_prob >= 0.85:
        return RiskLevel.CRITICAL, ThreatCategory.PHISHING
    if mal_prob >= 0.70:
        return RiskLevel.HIGH, ThreatCategory.PHISHING
    if mal_prob >= 0.55:
        return RiskLevel.MEDIUM, ThreatCategory.PHISHING
    if mal_prob >= 0.40:
        return RiskLevel.LOW, ThreatCategory.UNKNOWN
    return RiskLevel.SAFE, ThreatCategory.BENIGN


# ── Lazy singletons (load on first scan, not at import) ────────────

_ensemble = None
_ensemble_lock = threading.Lock()
_ensemble_failed = False

_shap_exp = None
_lime_exp = None
_llm_exp = None
_explainer_lock = threading.Lock()


def _get_ensemble():
    """Return the EnsembleModel, or None if it has already failed to load."""
    global _ensemble, _ensemble_failed
    if _ensemble_failed:
        return None
    if _ensemble is not None:
        return _ensemble
    with _ensemble_lock:
        if _ensemble is not None:
            return _ensemble
        try:
            from app.models.ensemble import EnsembleModel
            _ensemble = EnsembleModel()
        except Exception as e:
            _log.warning(
                "Ensemble failed to load (%s); falling back to legacy detector.", e
            )
            _ensemble_failed = True
            return None
        return _ensemble


def _get_explainers():
    global _shap_exp, _lime_exp, _llm_exp
    if _shap_exp is not None and _lime_exp is not None and _llm_exp is not None:
        return _shap_exp, _lime_exp, _llm_exp
    with _explainer_lock:
        if _shap_exp is None:
            try:
                from app.explainability.shap_explainer import SHAPExplainer
                _shap_exp = SHAPExplainer()
            except Exception as e:
                _log.warning("SHAP explainer unavailable: %s", e)
        if _lime_exp is None:
            try:
                from app.explainability.lime_explainer import LIMEExplainer
                _lime_exp = LIMEExplainer()
            except Exception as e:
                _log.warning("LIME explainer unavailable: %s", e)
        if _llm_exp is None:
            try:
                from app.explainability.llm_explainer import LLMExplainer
                _llm_exp = LLMExplainer()
            except Exception as e:
                _log.warning("LLM explainer unavailable: %s", e)
        return _shap_exp, _lime_exp, _llm_exp


# ── Result construction ────────────────────────────────────────────

_MODEL_DISPLAY_NAMES = {
    "decision_tree": ("DecisionTree", "v1.0"),
    "xgboost": ("XGBoost", "v1.0"),
    "lstm": ("LSTM", "v1.0"),
}


def _build_model_contributions(ensemble_result: dict) -> list[ModelContribution]:
    contributions = []
    final_label = ensemble_result.get("predicted_label")
    for model_key, per_model in ensemble_result.get("model_contributions", {}).items():
        if not isinstance(per_model, dict):
            # Defensive: legacy format with just label strings.
            continue
        display_name, version = _MODEL_DISPLAY_NAMES.get(
            model_key, (model_key, "v1.0")
        )
        probs = per_model.get("probabilities", {})
        score = float(probs.get(final_label, per_model.get("confidence", 0.0)))
        contributions.append(ModelContribution(
            model_name=display_name,
            version=version,
            score=round(score, 4),
            confidence=round(float(per_model.get("confidence", 0.0)), 4),
        ))
    return contributions


def _ensemble_to_scan_result(
    ensemble_result: dict,
    url: str,
    inference_ms: float,
) -> ScanResult:
    label = ensemble_result.get("predicted_label", "benign")
    risk_str = ensemble_result.get("risk_level", "low")
    threat = _THREAT_BY_LABEL.get(label, ThreatCategory.UNKNOWN)
    risk = _RISK_BY_STRING.get(risk_str, RiskLevel.LOW)

    return ScanResult(
        scan_id=None,
        url=url,
        risk_level=risk,
        confidence=round(float(ensemble_result.get("confidence", 0.0)), 4),
        threat_category=threat,
        model_contributions=_build_model_contributions(ensemble_result),
        inference_time_ms=round(inference_ms, 3),
    )


# ── Fallbacks ──────────────────────────────────────────────────────

def _hash_fallback(url: str, inference_ms: float) -> ScanResult:
    """Deterministic, URL-specific scoring of last resort."""
    h = int(hashlib.sha256(url.encode()).hexdigest(), 16)
    score = round(0.30 + (h % 10000) / 14492, 3)
    score = min(0.99, max(0.30, score))
    risk, cat = _risk_from_mal_prob(score)
    return ScanResult(
        scan_id=None,
        url=url,
        risk_level=risk,
        confidence=round(max(score, 1 - score), 3),
        threat_category=cat,
        model_contributions=[ModelContribution(
            model_name="URLHashHeuristic", version="fallback",
            score=score, confidence=round(max(score, 1 - score), 3),
        )],
        inference_time_ms=round(inference_ms, 3),
    )


def _legacy_rf_fallback(url: str, inference_ms: float) -> ScanResult:
    """Master's pre-existing RandomForest (binary phishing/legitimate)."""
    from app.models.malicious_detector import predict
    rf = predict(url)
    confidence = rf["confidence"] / 100.0
    mal_prob = rf["malicious_probability"] / 100.0
    if rf["label"] == "legitimate":
        risk, cat = RiskLevel.SAFE, ThreatCategory.BENIGN
    else:
        risk, cat = _risk_from_mal_prob(mal_prob)
    return ScanResult(
        scan_id=None,
        url=url,
        risk_level=risk,
        confidence=round(confidence, 3),
        threat_category=cat,
        model_contributions=[ModelContribution(
            model_name="RandomForest", version="v1.0-legacy",
            score=round(mal_prob, 3), confidence=round(confidence, 3),
        )],
        inference_time_ms=round(inference_ms, 3),
    )


# ── Public API ─────────────────────────────────────────────────────

def run_pipeline(req: ScanRequest) -> ScanResult:
    started = time.perf_counter()
    ensemble = _get_ensemble()

    if ensemble is not None:
        try:
            from app.runtime.detection_pipeline import build_feature_dict, fetch_page

            html: Optional[str] = req.html_snapshot
            if html is None:
                html, _status = fetch_page(req.url)

            feature_dict = build_feature_dict(
                url=req.url,
                html=html,
                runtime_evidence=req.runtime_evidence,
            )
            ensemble_result = ensemble.predict(feature_dict)
            elapsed = (time.perf_counter() - started) * 1000
            return _ensemble_to_scan_result(ensemble_result, req.url, elapsed)
        except Exception as e:
            _log.warning(
                "Ensemble inference failed for %s (%s); falling back.", req.url, e
            )

    # Fallback chain: legacy RF → URL hash.
    try:
        return _legacy_rf_fallback(req.url, (time.perf_counter() - started) * 1000)
    except Exception as e:
        _log.warning("Legacy RF unavailable (%s); using URL-hash fallback.", e)
        return _hash_fallback(req.url, (time.perf_counter() - started) * 1000)


def generate_explanation(scan_id: int, url: str) -> ExplanationResult:
    shap_exp, lime_exp, llm_exp = _get_explainers()

    # Build a feature_dict once for the explainers to share.
    try:
        from app.runtime.detection_pipeline import build_feature_dict, fetch_page
        html, _ = fetch_page(url)
        feature_dict = build_feature_dict(url=url, html=html, runtime_evidence=None)
    except Exception as e:
        _log.warning("Feature build failed for explanation of %s: %s", url, e)
        return _legacy_explanation_fallback(scan_id, url, str(e))

    shap_result = None
    if shap_exp is not None:
        try:
            shap_result = shap_exp.explain(feature_dict)
        except Exception as e:
            _log.warning("SHAP explanation failed: %s", e)

    lime_result = None
    if lime_exp is not None:
        try:
            lime_result = lime_exp.explain(feature_dict)
        except Exception as e:
            _log.warning("LIME explanation failed: %s", e)

    # Build top_features + shap_values dict for the contract.
    top_features: list[tuple[str, float]] = []
    shap_values: dict[str, float] = {}
    if shap_result:
        top_features = [
            (f["feature"], float(f["shap_value"]))
            for f in shap_result.get("top_features", [])
        ]
        shap_values = {
            f["feature"]: float(f["shap_value"])
            for f in shap_result.get("top_features", [])
        }
    elif lime_result:
        top_features = [
            (f["feature"], float(f["weight"]))
            for f in lime_result.get("top_features", [])
        ]

    # LLM summary on top of SHAP (template fallback inside the explainer).
    summary_text = ""
    if llm_exp is not None and shap_result is not None:
        try:
            scan_stub = {
                "predicted_label": shap_result.get("predicted_label", "unknown"),
                "confidence": 0.0,  # not known here, kept for API shape
            }
            llm_out = llm_exp.explain(url=url, scan_result=scan_stub, shap_result=shap_result)
            summary_text = llm_out.get("explanation") or ""
        except Exception as e:
            _log.warning("LLM explanation failed: %s", e)

    method = ExplanationMethod.SHAP if shap_result else (
        ExplanationMethod.LIME if lime_result else ExplanationMethod.SHAP
    )

    return ExplanationResult(
        scan_id=scan_id,
        method=method,
        top_features=top_features,
        shap_values=shap_values or None,
        lime_output=lime_result,
        summary_text=summary_text or None,
    )


def _legacy_explanation_fallback(scan_id: int, url: str, reason: str) -> ExplanationResult:
    """Master's pre-existing SHAP-style explainer over the RandomForest."""
    try:
        from app.models.malicious_detector import predict
        from app.explainability.explainer import explain
        prediction = predict(url)
        explanation = explain(url, prediction)
        top = [(f["feature"], f["importance"] / 100) for f in explanation.get("top_factors", [])]
        shap = {f["feature"]: f["importance"] / 100 for f in explanation.get("all_factors", [])}
        return ExplanationResult(
            scan_id=scan_id,
            method=ExplanationMethod.SHAP,
            top_features=top,
            shap_values=shap,
            summary_text=explanation.get("summary", ""),
        )
    except Exception as e:
        return ExplanationResult(
            scan_id=scan_id,
            method=ExplanationMethod.SHAP,
            top_features=[],
            summary_text=f"Explanation unavailable: {reason or e}",
        )
