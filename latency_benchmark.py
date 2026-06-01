"""Latency benchmark for the real ensemble.

Times cold load (artifact deserialization + first inference) separately
from warm inferences across a small URL panel that's distinct from the
training set, so the numbers reflect production-like usage rather than
re-running the train rows.
"""
from __future__ import annotations

import os
import statistics
import sys
import time

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import create_app  # noqa: E402
from app.interfaces.contracts import ScanRequest  # noqa: E402
from app.interfaces.pipeline import run_pipeline  # noqa: E402


# Picked to be non-training URLs across all four classes.
PANEL = [
    "https://www.wikipedia.org",
    "https://github.com/anthropics",
    "http://paypal-secure-login.tk/verify",
    "http://free-bitcoin-win.xyz/claim",
    "http://192.168.1.1/admin/login",
    "https://stackoverflow.com/questions/12345",
    "http://malware-install.top/setup.exe",
    "http://br-icloud.com.br",
    "https://docs.python.org/3/library",
    "http://amazon-security-alert.xyz/verify",
]

WARMUPS = 2
ROUNDS = 3


def main() -> int:
    app = create_app()
    with app.app_context():
        # ── Cold load: first call triggers artifact deserialization. ──
        cold_start = time.perf_counter()
        _ = run_pipeline(ScanRequest(url=PANEL[0]))
        cold_ms = (time.perf_counter() - cold_start) * 1000
        print(f"Cold load + first inference: {cold_ms:.0f} ms")

        # ── Warm panel ──
        for _ in range(WARMUPS):
            for url in PANEL:
                run_pipeline(ScanRequest(url=url))

        per_url_samples: dict[str, list[float]] = {url: [] for url in PANEL}
        for _ in range(ROUNDS):
            for url in PANEL:
                t0 = time.perf_counter()
                run_pipeline(ScanRequest(url=url))
                per_url_samples[url].append((time.perf_counter() - t0) * 1000)

        flat = [s for samples in per_url_samples.values() for s in samples]
        print(f"\nWarm inference over {len(flat)} runs:")
        print(f"  mean   = {statistics.mean(flat):.1f} ms")
        print(f"  median = {statistics.median(flat):.1f} ms")
        print(f"  p90    = {sorted(flat)[int(len(flat) * 0.9)]:.1f} ms")
        print(f"  max    = {max(flat):.1f} ms")
        print(f"  throughput ~ {1000 / statistics.mean(flat):.1f} scans/sec")

        print("\nPer-URL median:")
        for url, samples in per_url_samples.items():
            med = statistics.median(samples)
            print(f"  {med:>6.1f} ms   {url}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
