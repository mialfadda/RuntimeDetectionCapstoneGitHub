"""Phase 1 GATE: prove the model + scaler + feature ORDER are correct.

We bypass `build_feature_dict` entirely. The CSV at data/dataset.csv has
the same 42 columns as `feature_names.pkl` — those are exactly the
features each model was trained on. Feed those values directly through
each model wrapper's predict() path. If labels reproduce and overall
agreement on a random sample is high, the ensemble pipeline is sound
and the remaining problem is purely the runtime feature builder. If
not, stop and diagnose model loading / scaling / feature order / LSTM.

Run from repo root:
    python -m scripts.isolation_test
"""
from __future__ import annotations

import os
import sys

import joblib
import numpy as np
import pandas as pd

DATASET_PATH = os.environ.get("DATASET_PATH", "data/dataset.csv")
SAMPLE_N = 2000
RNG_SEED = 42

# Strings the report referenced. CSV may store them with/without scheme.
REPORT_REFERENCES = [
    ("824555.com/app/member/SportOption.php", "malware", 0.97),
    ("mp3raid.com",                            "benign", 0.82),
    ("br-icloud.com.br",                       "benign", 0.58),
]

LABEL_BY_INT = {0: "benign", 1: "defacement", 2: "phishing", 3: "malware"}


# -- Helpers --------------------------------------------------------


def _normalize(u: str) -> str:
    """Strip scheme / trailing slash / leading www., lowercase."""
    if not isinstance(u, str):
        return ""
    s = u.strip().lower()
    for prefix in ("https://", "http://"):
        if s.startswith(prefix):
            s = s[len(prefix):]
            break
    if s.startswith("www."):
        s = s[4:]
    return s.rstrip("/")


def _row_to_feature_dict(row: pd.Series, feature_names: list[str]) -> dict:
    """Read the canonical features straight off the CSV row."""
    return {fn: row.get(fn, 0) for fn in feature_names}


# -- Loaders --------------------------------------------------------


def _load_models_or_die():
    """Instantiate all three wrappers. If any silently fails to load
    we want to know NOW, not after a wrong-looking accuracy number."""
    try:
        from app.models.decision_tree_model import DecisionTreeModel
        dt = DecisionTreeModel()
        assert dt.model is not None
        assert list(dt.feature_names) is not None and len(dt.feature_names) == 42
    except Exception as e:
        sys.exit(f"FATAL: DecisionTreeModel failed to load: {e}")

    try:
        from app.models.xgboost_model import XGBoostModel
        xgb = XGBoostModel()
        assert xgb.model is not None
    except Exception as e:
        sys.exit(f"FATAL: XGBoostModel failed to load: {e}")

    try:
        from app.models.lstm_model import LSTMModel
        lstm = LSTMModel()
        # Keras model objects should expose .predict
        assert hasattr(lstm.model, "predict"), "LSTM .model has no .predict — silent load failure"
        assert lstm.scaler is not None and hasattr(lstm.scaler, "transform"), \
            "LSTM scaler missing or unusable"
    except Exception as e:
        sys.exit(f"FATAL: LSTMModel failed to load: {e}")

    from app.models.ensemble import EnsembleModel
    ens = EnsembleModel()
    return dt, xgb, lstm, ens


# -- Checks ---------------------------------------------------------


def check_a_reference_urls(df: pd.DataFrame, ens, feature_names: list[str]) -> bool:
    """Find each of the report URLs in the CSV and feed its row to predict."""
    print("-" * 76)
    print("Check A — three reference URLs")
    print("-" * 76)
    norm_index = df["url"].map(_normalize)
    all_ok = True

    for url, expected_label, expected_conf in REPORT_REFERENCES:
        target = _normalize(url)
        hits = df[norm_index == target]
        if hits.empty:
            # Try a substring fallback so a longer path version still matches.
            hits = df[norm_index.str.startswith(target, na=False)]
        if hits.empty:
            print(f"  [!] {url}: NOT FOUND in CSV — skipping")
            continue

        row = hits.iloc[0]
        feature_dict = _row_to_feature_dict(row, feature_names)
        result = ens.predict(feature_dict)
        got_label = result["predicted_label"]
        got_conf = result["confidence"]
        csv_truth = row.get("type", "?")

        label_match = got_label == expected_label
        conf_close = abs(got_conf - expected_conf) <= 0.05
        ok = label_match and conf_close
        mark = "OK" if ok else "  "
        print(
            f"  [{mark}] {url}"
            f"\n        CSV row truth     = {csv_truth}"
            f"\n        Report expects    = {expected_label} (~{expected_conf:.2f})"
            f"\n        Got from ensemble = {got_label} (~{got_conf:.2f})"
        )
        if not ok:
            all_ok = False
            if not label_match:
                print(f"        [X] label mismatch")
            if not conf_close:
                print(f"        [X] confidence off by {abs(got_conf - expected_conf):.3f} (>0.05)")
    return all_ok


def check_b_random_sample(df: pd.DataFrame, dt, xgb, lstm, ens,
                          feature_names: list[str]) -> tuple[bool, dict]:
    """Predict on N random rows from the CSV; report per-model agreement
    against the row's true 4-class label."""
    print("-" * 76)
    print(f"Check B — random sample of {SAMPLE_N} rows")
    print("-" * 76)
    sample = df.sample(n=min(SAMPLE_N, len(df)), random_state=RNG_SEED)
    sample = sample[sample["type"].isin(LABEL_BY_INT.values())]  # safety

    correct = {"decision_tree": 0, "xgboost": 0, "lstm": 0, "ensemble": 0}
    confusion = {label: {label2: 0 for label2 in LABEL_BY_INT.values()}
                 for label in LABEL_BY_INT.values()}
    n = 0

    for _, row in sample.iterrows():
        truth = row["type"]
        if truth not in LABEL_BY_INT.values():
            continue
        feature_dict = _row_to_feature_dict(row, feature_names)
        ens_result = ens.predict(feature_dict)
        if ens_result["predicted_label"] == truth:
            correct["ensemble"] += 1
        confusion[truth][ens_result["predicted_label"]] += 1

        # Per-model agreement from the contributions to avoid 3x re-predict.
        for model_key in ("decision_tree", "xgboost", "lstm"):
            per_model = ens_result["model_contributions"][model_key]
            if per_model["predicted_label"] == truth:
                correct[model_key] += 1
        n += 1

    print(f"  evaluated {n} rows ({len(sample) - n} skipped for unexpected type)\n")
    print("  per-model accuracy:")
    for k, v in correct.items():
        acc = v / n if n else 0
        flag = "[OK]" if acc >= 0.5 else "[X]"
        print(f"    {flag} {k:<14s} {acc*100:6.2f}%  ({v}/{n})")

    print("\n  ensemble confusion matrix (rows=truth, cols=pred):")
    header = " " * 13 + "".join(f"{c:>11}" for c in LABEL_BY_INT.values())
    print(header)
    for truth_label in LABEL_BY_INT.values():
        row_total = sum(confusion[truth_label].values()) or 1
        cells = "".join(
            f"{confusion[truth_label][pred]:>5} ({confusion[truth_label][pred]*100//row_total:>2}%)"
            for pred in LABEL_BY_INT.values()
        )
        print(f"    {truth_label:<10}{cells}")

    ensemble_acc = correct["ensemble"] / n if n else 0
    # Pass if ensemble agrees with truth ≥75% — well above the 25% random baseline,
    # below the report's headline ~89% so we don't punish small dataset drift.
    passed = ensemble_acc >= 0.75
    return passed, {"n": n, "accuracy": correct, "confusion": confusion}


# -- Main -----------------------------------------------------------


def main() -> int:
    if not os.path.exists(DATASET_PATH):
        sys.exit(f"FATAL: dataset not found at {DATASET_PATH}")

    feature_names = joblib.load("models/feature_names.pkl")
    print(f"feature_names.pkl: {len(feature_names)} columns (authoritative order)\n")

    print("Loading dataset...")
    df = pd.read_csv(DATASET_PATH, low_memory=False)
    print(f"  rows: {len(df):,}, columns: {len(df.columns)}")
    missing = [fn for fn in feature_names if fn not in df.columns]
    if missing:
        sys.exit(f"FATAL: CSV missing {len(missing)} feature columns: {missing[:8]}")
    print(f"  all {len(feature_names)} feature columns present in CSV [OK]")

    if "url" not in df.columns or "type" not in df.columns:
        sys.exit("FATAL: CSV missing 'url' or 'type' column")

    truth_counts = df["type"].value_counts()
    print(f"  class balance: {dict(truth_counts)}\n")

    print("Loading models...")
    dt, xgb, lstm, ens = _load_models_or_die()
    print("  all three models + ensemble loaded [OK]\n")

    check_a_ok = check_a_reference_urls(df, ens, feature_names)
    print()
    check_b_ok, _ = check_b_random_sample(df, dt, xgb, lstm, ens, feature_names)

    print("\n" + "=" * 76)
    if check_a_ok and check_b_ok:
        print(" GATE PASS — model/scaler/feature-order verified. Phase 3 unblocked.")
        return 0

    print(" GATE FAIL — model/scaler/feature-order isn't producing the expected")
    print(" predictions even with CSV-truth features. STOP and diagnose:")
    print("    - is `type` actually the 4-class string column?")
    print("    - is `feature_names.pkl` order honored by the model wrappers?")
    print("    - did LSTM load? (silent .keras failure would halve the ensemble)")
    print("    - is the scaler the one saved at training time?")
    return 1


if __name__ == "__main__":
    sys.exit(main())
