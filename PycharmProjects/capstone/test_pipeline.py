import sys
sys.path.insert(0, '/Users/aljohara/PycharmProjects/capstone')

from backend.app.interfaces.contracts import ScanRequest
from backend.app.runtime.detection_pipeline import run_detection

# Test 1 — a suspicious URL
print("=" * 60)
print("TEST 1: Suspicious URL")
print("=" * 60)
request1 = ScanRequest(url="http://br-icloud.com.br")
result1 = run_detection(request1)
print(result1.to_dict())

# Test 2 — a normal URL
print("\n" + "=" * 60)
print("TEST 2: Normal URL")
print("=" * 60)
request2 = ScanRequest(url="https://www.google.com")
result2 = run_detection(request2)
print(result2.to_dict())

# Note: short clean URLs (google.com) may show false positives
# with URL-only features. Runtime evidence from the browser
# extension (A1) will significantly improve accuracy in production.