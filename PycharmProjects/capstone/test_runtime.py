import sys
sys.path.insert(0, '/Users/aljohara/PycharmProjects/capstone')

from backend.app.runtime.runtime_monitor import RuntimeEvidence, extract_runtime_features

# Simulate a clean page
clean = RuntimeEvidence(
    js_api_calls=["document.getElementById", "console.log"],
    dom_mutation_count=3,
    network_requests=["https://cdn.mysite.com/style.css"],
    execution_time_ms=120.0
)

# Simulate a malicious page
malicious = RuntimeEvidence(
    js_api_calls=["document.cookie", "eval(payload)", "atob(encoded)", "localStorage.setItem"],
    dom_mutation_count=47,
    network_requests=["http://tracker.evil.com", "http://steal.com/data", "https://cdn.com/x.js"],
    execution_time_ms=890.0
)

print("--- Clean Page ---")
print(extract_runtime_features(clean))

print("\n--- Malicious Page ---")
print(extract_runtime_features(malicious))