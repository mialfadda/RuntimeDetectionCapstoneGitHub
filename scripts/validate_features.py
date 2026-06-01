"""Phase 3 validation: per-column exact-match rate of the new extractor.

Loads the CSV, runs `extract_features_from_url` on each row's `url`, and
reports how often each of the 42 features matches the CSV value exactly.
The CSV is GROUND TRUTH — never adjust the model/scaler/thresholds to
paper over a mismatch; iterate the extractor or its lists.

Targets:
  - Structural URL columns (counts, lengths, IP detection): 100%
  - List/keyword-based columns (TLDs, brands, keywords):    ≥ 99%

Run from repo root:
    python -m scripts.validate_features
Optionally:
    SAMPLE=20000 python -m scripts.validate_features
"""
from __future__ import annotations

import os
import sys

import joblib
import pandas as pd

from app.runtime.features import extract_features_from_url

DATASET_PATH = os.environ.get("DATASET_PATH", "data/dataset.csv")
SAMPLE = int(os.environ.get("SAMPLE", "30000"))  # large sample by default
DEBUG_K = 5  # how many mismatched examples to print per failing column


# Columns that come from URL structure (must hit 100%).
STRUCTURAL = {
    "url_len", "@", "?", "-", "=", ".", "#", "%", "+", "$", "!", "*",
    ",", "//", "digits", "letters", "having_ip_address",
    "phish_adv_encoded_chars", "phish_adv_many_params",
    "path_underscore_count",
}

# Columns derived from inferred lists/thresholds (target ≥99%).
LIST_BASED = {
    "Shortining_Service", "phish_urgency_words", "phish_security_words",
    "phish_brand_mentions", "phish_brand_hijack",
    "phish_multiple_subdomains", "phish_long_path", "phish_many_params",
    "phish_suspicious_tld", "phish_adv_exact_brand_match",
    "phish_adv_brand_in_subdomain", "phish_adv_brand_in_path",
    "phish_adv_hyphen_count", "phish_adv_number_count",
    "phish_adv_suspicious_tld", "phish_adv_long_domain",
    "phish_adv_many_subdomains", "phish_adv_path_keywords",
    "phish_adv_has_redirect", "path_has_hacked_terms",
    "suspicious_extension", "is_gov_edu",
}


def main() -> int:
    if not os.path.exists(DATASET_PATH):
        sys.exit(f"FATAL: dataset not found at {DATASET_PATH}")

    feature_names = list(joblib.load("models/feature_names.pkl"))
    print(f"feature_names.pkl: {len(feature_names)} columns")

    print(f"Loading dataset (SAMPLE={SAMPLE}) ...")
    df_full = pd.read_csv(DATASET_PATH, low_memory=False)
    df = df_full.sample(n=min(SAMPLE, len(df_full)), random_state=42).reset_index(drop=True)
    print(f"  evaluating {len(df):,} rows")

    print("Running extractor...")
    extracted = df["url"].astype(str).map(extract_features_from_url)
    ext_df = pd.DataFrame(list(extracted))

    rows = []
    mismatched_examples: dict[str, list[tuple[str, object, object]]] = {}
    for col in feature_names:
        if col not in ext_df.columns:
            rows.append((col, 0.0, len(df), "MISSING from extractor"))
            continue
        truth = df[col]
        got = ext_df[col]
        # Compare as plain Python values to tolerate dtype quirks.
        match = (truth.astype(float).round(6) == got.astype(float).round(6))
        rate = float(match.mean())
        miscount = int((~match).sum())

        category = "structural" if col in STRUCTURAL else (
            "list-based" if col in LIST_BASED else "uncategorized"
        )
        rows.append((col, rate, miscount, category))

        if rate < 1.0:
            bad_idx = (~match).to_numpy().nonzero()[0][:DEBUG_K]
            mismatched_examples[col] = [
                (df.loc[i, "url"], truth.iloc[i], got.iloc[i])
                for i in bad_idx
            ]

    # Sort by rate ascending (worst first).
    rows.sort(key=lambda r: r[1])
    print()
    print(f"{'column':<35s} {'match%':>8s}  {'#bad':>7s}  category")
    print("-" * 80)
    structural_pass = True
    list_pass = True
    for col, rate, miscount, category in rows:
        ok = rate == 1.0 if category == "structural" else rate >= 0.99
        mark = "[OK]" if ok else "[X] "
        print(f"{mark} {col:<32s} {rate*100:7.3f}%  {miscount:>7d}  {category}")
        if category == "structural" and rate < 1.0:
            structural_pass = False
        if category == "list-based" and rate < 0.99:
            list_pass = False

    print()
    print("=" * 80)
    if structural_pass and list_pass:
        print(" VALIDATION PASS — extractor reproduces the CSV within targets.")
    else:
        print(" VALIDATION INCOMPLETE:")
        if not structural_pass:
            print("   - one or more STRUCTURAL columns below 100%; check parsing.")
        if not list_pass:
            print("   - one or more LIST-BASED columns below 99%; iterate the lists.")
        print()
        print("Worst-matching columns + sample mismatches (first {} per column):".format(DEBUG_K))
        # Show debug for the 10 lowest-rate columns.
        for col, rate, _, _ in rows[:10]:
            if rate >= 1.0:
                break
            print(f"\n  >> {col}  ({rate*100:.2f}%)")
            for url, truth, got in mismatched_examples.get(col, []):
                print(f"       truth={truth!r:>10}  got={got!r:>10}  url={url[:120]}")

    return 0 if (structural_pass and list_pass) else 1


if __name__ == "__main__":
    sys.exit(main())
