"""End-to-end runtime-vs-CSV parity check.

For each reference URL, compare three things side-by-side:
  (a) Runtime path:  extract_features_from_url(url) -> ensemble.predict()
  (b) CSV-row path:  read the row's 42 pre-computed features straight off
                     the CSV -> ensemble.predict()  (this is what the
                     model actually evaluates against — Phase 1 GATE)
  (c) CSV ground-truth label (for context only)

PASS = (a) reproduces (b). The CSV ground-truth label is reported
separately so the report can note "model's known miss on URL X" without
the parity check rewarding feature-bugs that happen to flip the label
the "right" way.

Run from repo root:
    python feature_alignment_check.py
"""
from __future__ import annotations

import os
import sys

import joblib
import pandas as pd

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import create_app  # noqa: E402
from app.models.ensemble import EnsembleModel  # noqa: E402
from app.runtime.features import extract_features_from_url  # noqa: E402

DATASET_PATH = os.environ.get("DATASET_PATH", "data/dataset.csv")
CONF_TOLERANCE = 0.02  # acceptable confidence drift between (a) and (b)

# The three URLs the report references. Each is a substring matched
# against `df['url']` so we hit whichever form the CSV happens to store.
REFERENCES = [
    "824555.com/app/member/SportOption.php",
    "mp3raid.com/music/krizz_kaliko.html",
    "br-icloud.com.br",
]


def _ensure_app_context():
    app = create_app()
    return app


def _predict(ensemble: EnsembleModel, feature_dict: dict) -> tuple[str, float, dict]:
    result = ensemble.predict(feature_dict)
    return result["predicted_label"], result["confidence"], result


def _row_feature_dict(row: pd.Series, feature_names: list[str]) -> dict:
    return {fn: row.get(fn, 0) for fn in feature_names}


def main() -> int:
    if not os.path.exists(DATASET_PATH):
        sys.exit(f"FATAL: dataset not found at {DATASET_PATH}")
    feature_names = list(joblib.load("models/feature_names.pkl"))

    print("Loading dataset...")
    df = pd.read_csv(DATASET_PATH, low_memory=False)

    print("Loading ensemble...")
    app = _ensure_app_context()
    with app.app_context():
        ensemble = EnsembleModel()

        print()
        print("=" * 90)
        print(f"{'URL':<55s}  {'runtime':<20s}  {'csv-row':<20s}")
        print("-" * 90)

        all_match = True
        details = []

        for query in REFERENCES:
            hits = df[df["url"].str.contains(query, regex=False, case=False, na=False)]
            if hits.empty:
                print(f"  [!]  {query}: NOT FOUND in CSV (skipped)")
                continue
            row = hits.iloc[0]
            csv_url = row["url"]
            truth_label = row.get("type", "?")

            # (a) Runtime path
            runtime_feats = extract_features_from_url(csv_url)
            r_label, r_conf, r_result = _predict(ensemble, runtime_feats)

            # (b) CSV-row path
            csv_feats = _row_feature_dict(row, feature_names)
            c_label, c_conf, c_result = _predict(ensemble, csv_feats)

            label_match = (r_label == c_label)
            conf_match = abs(r_conf - c_conf) <= CONF_TOLERANCE
            ok = label_match and conf_match

            tag = "[OK]" if ok else "[X] "
            short = csv_url if len(csv_url) <= 53 else csv_url[:50] + "..."
            note = f"(csv truth: {truth_label})"
            if not all_match or not ok:
                pass
            print(f"  {tag} {short:<53s}  "
                  f"{r_label:<10s} {r_conf:>5.2f}    "
                  f"{c_label:<10s} {c_conf:>5.2f}    {note}")

            if not ok:
                all_match = False
                details.append((csv_url, runtime_feats, csv_feats, feature_names, truth_label))

        print("=" * 90)

        # Per-feature deltas for any (a) != (b) case
        for csv_url, rt, csvf, fns, truth in details:
            print()
            print(f"Diagnostic deltas for: {csv_url}")
            print(f"  (CSV ground-truth label: {truth})")
            for fn in fns:
                rv = rt.get(fn)
                cv = csvf.get(fn)
                try:
                    if float(rv) != float(cv):
                        print(f"     {fn:<32s}  runtime={rv}  csv={cv}")
                except Exception:
                    if rv != cv:
                        print(f"     {fn:<32s}  runtime={rv!r}  csv={cv!r}")

        print()
        if all_match:
            print("PARITY PASS: runtime reproduces the model's prediction on every")
            print("reference URL's CSV-row features (within "
                  f"|delta_conf| <= {CONF_TOLERANCE}). Where the model's prediction")
            print("disagrees with CSV ground truth, that disagreement is the model's")
            print("known miss, not a runtime bug.")
            return 0

        print("PARITY FAIL: one or more reference URLs have a runtime prediction")
        print("that diverges from the model's CSV-row prediction. The deltas above")
        print("identify which features still differ between the extractor and the")
        print("CSV. The CSV is ground truth for the feature representation; iterate")
        print("the extractor, not the model.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
