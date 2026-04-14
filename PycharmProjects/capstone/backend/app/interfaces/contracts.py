from dataclasses import dataclass, field
from typing import Optional, List, Dict


# ── Input Contracts ──────────────────────────────────────

@dataclass
class RuntimeEvidence:
    """
    Runtime behavior data collected by the browser extension (A1).
    Optional — not all scans will have runtime evidence.
    """
    js_api_calls: List[str] = field(default_factory=list)
    dom_mutation_count: int = 0
    network_requests: List[str] = field(default_factory=list)
    execution_time_ms: float = 0.0


@dataclass
class ScanRequest:
    """
    Input to the detection pipeline.
    Contains the URL to scan and optional runtime evidence.
    """
    url: str
    runtime_evidence: Optional[RuntimeEvidence] = None
    user_id: Optional[str] = None
    scan_id: Optional[str] = None


# ── Output Contracts ─────────────────────────────────────

@dataclass
class FeatureVector:
    """
    Combined features extracted from URL, HTML and runtime.
    Produced by B1, consumed by B2's models.
    """
    # URL features
    url_length: int = 0
    subdomain_count: int = 0
    path_depth: int = 0
    special_char_count: int = 0
    has_ip_address: int = 0
    is_url_shortener: int = 0
    has_suspicious_keywords: int = 0
    is_https: int = 0
    num_digits_in_url: int = 0
    num_dots: int = 0
    num_hyphens: int = 0
    has_at_symbol: int = 0
    has_double_slash_redirect: int = 0
    domain_length: int = 0

    # HTML features
    num_forms: int = 0
    num_inputs: int = 0
    has_password_field: int = 0
    num_external_links: int = 0
    num_total_links: int = 0
    num_scripts: int = 0
    suspicious_script_count: int = 0
    num_iframes: int = 0
    num_hidden_elements: int = 0
    num_meta_tags: int = 0
    has_favicon: int = 0
    has_redirect_meta: int = 0
    title_length: int = 0

    # Runtime features
    suspicious_api_call_count: int = 0
    total_api_call_count: int = 0
    dom_mutation_count: int = 0
    external_request_count: int = 0
    total_network_requests: int = 0
    execution_time_ms: float = 0.0

    def to_dict(self) -> dict:
        return self.__dict__


@dataclass
class ModelContributions:
    """
    Individual predictions from each model in the ensemble.
    """
    decision_tree: str = ""
    xgboost: str = ""
    lstm: str = ""


@dataclass
class ScanResult:
    """
    Final output of the detection pipeline.
    Returned to A1's API endpoint.
    """
    scan_id: str
    url: str
    predicted_label: str           # benign / defacement / phishing / malware
    predicted_class: int           # 0 / 1 / 2 / 3
    confidence: float              # 0.0 - 1.0
    risk_level: str                # low / medium / high / critical
    final_probabilities: Dict[str, float] = field(default_factory=dict)
    model_contributions: Optional[ModelContributions] = None
    feature_vector: Optional[FeatureVector] = None
    error: Optional[str] = None    # populated if something went wrong

    def is_malicious(self) -> bool:
        return self.predicted_label != "benign"

    def to_dict(self) -> dict:
        return {
            "scan_id": self.scan_id,
            "url": self.url,
            "predicted_label": self.predicted_label,
            "predicted_class": self.predicted_class,
            "confidence": self.confidence,
            "risk_level": self.risk_level,
            "is_malicious": self.is_malicious(),
            "final_probabilities": self.final_probabilities,
            "model_contributions": self.model_contributions.__dict__
            if self.model_contributions else {},
            "error": self.error
        }