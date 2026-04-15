"""B-team mocks so A1 can develop /scan/analyze and /explanations before B1/B2 land.
Replace with real calls at Week 3 integration checkpoint."""
import time
from hashlib import sha1

from app.interfaces.contracts import (
    ExplanationMethod,
    ExplanationResult,
    ModelContribution,
    RiskLevel,
    ScanRequest,
    ScanResult,
    ThreatCategory,
)


def run_pipeline(req: ScanRequest) -> ScanResult:
    """Deterministic stand-in for B1's detection pipeline."""
    started = time.perf_counter()
    h = int(sha1(req.url.encode()).hexdigest(), 16)
    score = (h % 1000) / 1000.0
    if score < 0.4:
        level, cat = RiskLevel.SAFE, ThreatCategory.BENIGN
    elif score < 0.7:
        level, cat = RiskLevel.MEDIUM, ThreatCategory.PHISHING
    else:
        level, cat = RiskLevel.HIGH, ThreatCategory.MALWARE
    return ScanResult(
        scan_id=None,
        url=req.url,
        risk_level=level,
        confidence=round(score, 3),
        threat_category=cat,
        model_contributions=[
            ModelContribution("decision_tree", "mock-0.1", score, score),
            ModelContribution("lstm", "mock-0.1", score, score),
            ModelContribution("svm", "mock-0.1", score, score),
        ],
        inference_time_ms=round((time.perf_counter() - started) * 1000, 3),
    )


def generate_explanation(scan_id: int, url: str) -> ExplanationResult:
    """Stand-in for B2's SHAP/LIME/LLM output."""
    return ExplanationResult(
        scan_id=scan_id,
        method=ExplanationMethod.SHAP,
        top_features=[("url_length", 0.34), ("has_ip", 0.22), ("suspicious_tld", 0.18)],
        shap_values={"url_length": 0.34, "has_ip": 0.22, "suspicious_tld": 0.18},
        summary_text=f"URL {url} flagged due to length and suspicious TLD (mock).",
    )
