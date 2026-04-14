from dataclasses import dataclass, field
from typing import List


SUSPICIOUS_API_CALLS = [
    "document.cookie",
    "localStorage.setItem",
    "sessionStorage.setItem",
    "eval(",
    "atob(",
    "window.location.replace",
    "navigator.credentials",
]


@dataclass
class RuntimeEvidence:
    """
    Data structure received from the browser extension (A1).
    Contains runtime behavior observed while the page was loading.
    """
    js_api_calls: List[str] = field(default_factory=list)
    dom_mutation_count: int = 0
    network_requests: List[str] = field(default_factory=list)
    execution_time_ms: float = 0.0


def extract_runtime_features(evidence: RuntimeEvidence) -> dict:
    """
    Extracts features from runtime browser behavior.
    Returns a flat dictionary to be merged into the FeatureVector.
    """
    suspicious_call_count = sum(
        1 for call in evidence.js_api_calls
        if any(pattern in call for pattern in SUSPICIOUS_API_CALLS)
    )

    external_requests = [
        r for r in evidence.network_requests
        if r.startswith("http")
    ]

    return {
        "suspicious_api_call_count": suspicious_call_count,
        "total_api_call_count": len(evidence.js_api_calls),
        "dom_mutation_count": evidence.dom_mutation_count,
        "external_request_count": len(external_requests),
        "total_network_requests": len(evidence.network_requests),
        "execution_time_ms": evidence.execution_time_ms,
    }