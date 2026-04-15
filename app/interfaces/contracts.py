"""
Shared data contracts exchanged between API (A1), DB (A2), Pipeline (B1), and Models (B2).
Defined on Day 1 so each team can mock the others and work in parallel.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class RiskLevel(str, Enum):
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatCategory(str, Enum):
    BENIGN = "benign"
    PHISHING = "phishing"
    MALWARE = "malware"
    DEFACEMENT = "defacement"
    SPAM = "spam"
    UNKNOWN = "unknown"


class ExplanationMethod(str, Enum):
    SHAP = "shap"
    LIME = "lime"
    LLM = "llm"


@dataclass
class RuntimeEvidence:
    """Behavioural signals captured by the browser extension (B1 consumes)."""
    js_api_calls: list[str] = field(default_factory=list)
    dom_mutations: list[dict[str, Any]] = field(default_factory=list)
    network_requests: list[dict[str, Any]] = field(default_factory=list)
    timing_ms: Optional[float] = None


@dataclass
class ScanRequest:
    """A1 -> B1. Payload of POST /scan/analyze."""
    url: str
    user_id: Optional[int] = None
    html_snapshot: Optional[str] = None
    runtime_evidence: Optional[RuntimeEvidence] = None


@dataclass
class FeatureVector:
    """B1 -> B2. Extracted URL/HTML/behavioural features."""
    url_features: dict[str, float] = field(default_factory=dict)
    html_features: dict[str, float] = field(default_factory=dict)
    runtime_features: dict[str, float] = field(default_factory=dict)


@dataclass
class ModelContribution:
    model_name: str
    version: str
    score: float
    confidence: float


@dataclass
class ScanResult:
    """B1/B2 -> A1. Returned by POST /scan/analyze."""
    scan_id: Optional[int]
    url: str
    risk_level: RiskLevel
    confidence: float
    threat_category: ThreatCategory
    model_contributions: list[ModelContribution] = field(default_factory=list)
    inference_time_ms: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ExplanationResult:
    """B2 -> A1. Returned by /explanations endpoints."""
    scan_id: int
    method: ExplanationMethod
    top_features: list[tuple[str, float]] = field(default_factory=list)
    shap_values: Optional[dict[str, float]] = None
    lime_output: Optional[dict[str, Any]] = None
    summary_text: Optional[str] = None


def to_json(obj: Any) -> dict:
    """Serialize a dataclass contract to a JSON-ready dict."""
    if hasattr(obj, "__dataclass_fields__"):
        result = asdict(obj)
        for k, v in result.items():
            if isinstance(v, datetime):
                result[k] = v.isoformat()
            elif isinstance(v, Enum):
                result[k] = v.value
        return result
    return obj
