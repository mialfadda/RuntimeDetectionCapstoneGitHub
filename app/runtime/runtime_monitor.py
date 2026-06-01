"""Runtime-evidence feature extraction.

Accepts the master `RuntimeEvidence` dataclass (or any object exposing the
same attributes) and returns a dict ready to merge into the feature_dict.
"""
from typing import Any


SUSPICIOUS_API_CALLS = [
    "document.cookie",
    "localStorage.setItem",
    "sessionStorage.setItem",
    "eval(",
    "atob(",
    "window.location.replace",
    "navigator.credentials",
]


def extract_runtime_features(evidence: Any) -> dict:
    """Pull behavioural counts off a `RuntimeEvidence`.

    Tolerates both master's shape (`dom_mutations: list[dict]`, `timing_ms`)
    and main's (`dom_mutation_count: int`, `execution_time_ms`).
    """
    js_calls = getattr(evidence, "js_api_calls", []) or []
    suspicious_call_count = sum(
        1 for call in js_calls
        if any(pattern in call for pattern in SUSPICIOUS_API_CALLS)
    )

    raw_requests = getattr(evidence, "network_requests", []) or []
    external_requests = []
    for r in raw_requests:
        url = r if isinstance(r, str) else (r.get("url") if isinstance(r, dict) else "")
        if isinstance(url, str) and url.startswith("http"):
            external_requests.append(url)

    dom_mutations = getattr(evidence, "dom_mutations", None)
    if dom_mutations is None:
        dom_count = int(getattr(evidence, "dom_mutation_count", 0) or 0)
    else:
        dom_count = len(dom_mutations)

    timing = getattr(evidence, "timing_ms", None)
    if timing is None:
        timing = getattr(evidence, "execution_time_ms", 0.0) or 0.0

    return {
        "suspicious_api_call_count": suspicious_call_count,
        "total_api_call_count": len(js_calls),
        "dom_mutation_count": dom_count,
        "external_request_count": len(external_requests),
        "total_network_requests": len(raw_requests),
        "execution_time_ms": float(timing),
    }
