"""Feature-alignment sanity check.

Runs the three reference URLs from the project report through the
adapter end-to-end and prints (label, confidence, per-model probs).
Compare against the expected values from the report:

    824555.com/app/member/SportOption.php  ->  malware  ~0.97
    mp3raid.com                            ->  benign   ~0.82
    br-icloud.com.br                       ->  benign   ~0.58

If the numbers are wildly off, the feature_dict order or the scaler
is misaligned and the rest of the verify steps should be paused
until the mapping in `app/runtime/detection_pipeline.build_feature_dict`
is fixed.
"""
from __future__ import annotations

import os
import sys

# In-memory DB so Flask app boots without touching disk.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import create_app  # noqa: E402
from app.interfaces.contracts import ScanRequest  # noqa: E402
from app.interfaces.pipeline import run_pipeline  # noqa: E402


# Exact URL strings from data/dataset.csv (the integration spec quoted
# shortened forms; the runtime sees the full URL the dataset's pipeline
# computed features from).
REFERENCE = [
    ("http://824555.com/app/member/SportOption.php?uid=guest&langx=gb", "malware",  0.97),
    ("mp3raid.com/music/krizz_kaliko.html",                              "benign",   0.82),
    ("br-icloud.com.br",                                                 "benign",   0.58),
]


def main() -> int:
    app = create_app()
    rows = []
    with app.app_context():
        for url, expected_label, expected_conf in REFERENCE:
            result = run_pipeline(ScanRequest(url=url))
            rows.append({
                "url": url,
                "expected": (expected_label, expected_conf),
                "got_category": result.threat_category.value,
                "got_confidence": result.confidence,
                "got_risk": result.risk_level.value,
                "per_model": [
                    (mc.model_name, mc.score, mc.confidence)
                    for mc in (result.model_contributions or [])
                ],
                "inference_ms": result.inference_time_ms,
            })

    print(f"{'URL':<55}  {'EXPECTED':<22}  {'GOT':<22}  delta")
    print("-" * 110)
    max_delta = 0.0
    misaligned = []
    for r in rows:
        exp_label, exp_conf = r["expected"]
        got_label, got_conf = r["got_category"], r["got_confidence"]
        delta = got_conf - exp_conf if got_label == exp_label else float("nan")
        if got_label != exp_label or abs(delta) > 0.25:
            misaligned.append(r)
        max_delta = max(max_delta, abs(delta) if delta == delta else 0)
        print(f"{r['url']:<55}  {exp_label:<10}{exp_conf:>6.2f}     "
              f"{got_label:<10}{got_conf:>6.2f}     {delta:+.2f}"
              if delta == delta else
              f"{r['url']:<55}  {exp_label:<10}{exp_conf:>6.2f}     "
              f"{got_label:<10}{got_conf:>6.2f}     MISMATCH")
    print()
    for r in rows:
        print(f"  {r['url']}  ({r['inference_ms']:.0f} ms, risk={r['got_risk']})")
        for name, score, conf in r["per_model"]:
            print(f"    - {name:<14}  score={score:.4f}  confidence={conf:.4f}")

    if misaligned:
        print(f"\nWARNING: {len(misaligned)} URL(s) deviate from the report — "
              "feature_dict order or scaler may be misaligned.")
        return 1
    print("\nAll three reference URLs land within tolerance.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
