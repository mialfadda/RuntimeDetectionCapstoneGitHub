"""Phase 2: regenerate the report's accuracy table from the CSV.

Independent of the runtime feature builder — we use the dataset's
PRE-COMPUTED feature columns straight off the CSV, mirroring the
ported training pipeline's train/test split.

Inputs (all read at runtime, none hardcoded):
  - data/dataset.csv             — Kaggle "Enhanced 2026"
  - models/feature_names.pkl     — authoritative feature ORDER (42 cols)
  - models/scaler.pkl            — SAVED scaler (LSTM input only)
  - models/decision_tree.pkl, xgboost.pkl, lstm_model.keras

Outputs:
  - reports/accuracy_repro.md    — human-readable summary
  - reports/accuracy_repro.json  — machine-readable

Run from repo root:
    python -m scripts.reproduce_accuracy
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix,
)
from sklearn.model_selection import train_test_split

DATASET_PATH = os.environ.get("DATASET_PATH", "data/dataset.csv")
REPORTS_DIR = "reports"

# Mirrors app/models/training/train_models.py and train_lstm.py.
SPLIT = {"test_size": 0.2, "random_state": 42, "stratify_on": "label"}

LABEL_NAMES = ["benign", "defacement", "phishing", "malware"]
LABEL_INT = {name: i for i, name in enumerate(LABEL_NAMES)}

# The report's headline per-model accuracy (the integration spec's prose).
REPORT_TARGETS = {"decision_tree": 0.895, "xgboost": 0.88, "lstm": 0.87}
LARGE_DELTA = 0.05  # >5pp deviation from report = flag


def _load_inputs():
    if not os.path.exists(DATASET_PATH):
        sys.exit(f"FATAL: dataset not found at {DATASET_PATH}")

    feature_names = list(joblib.load("models/feature_names.pkl"))
    print(f"feature_names.pkl: {len(feature_names)} cols")
    scaler = joblib.load("models/scaler.pkl")
    print(f"scaler:            {type(scaler).__name__}")

    dt = joblib.load("models/decision_tree.pkl")
    xgb = joblib.load("models/xgboost.pkl")
    from tensorflow.keras.models import load_model
    lstm = load_model("models/lstm_model.keras")
    print(f"models loaded:     DT={type(dt).__name__}, "
          f"XGB={type(xgb).__name__}, LSTM={type(lstm).__name__}")

    print(f"Loading {DATASET_PATH} ...")
    df = pd.read_csv(DATASET_PATH, low_memory=False)
    print(f"  rows: {len(df):,}")

    missing = [fn for fn in feature_names if fn not in df.columns]
    if missing:
        sys.exit(f"FATAL: CSV missing feature cols: {missing[:8]}")
    if "label" not in df.columns:
        sys.exit("FATAL: CSV missing 'label' column (int 4-class target)")

    X = df[feature_names].apply(pd.to_numeric, errors="coerce").fillna(0)
    y = df["label"].astype(int)
    return feature_names, scaler, dt, xgb, lstm, X, y


def _split(X: pd.DataFrame, y: pd.Series):
    Xtr, Xte, ytr, yte = train_test_split(
        X, y,
        test_size=SPLIT["test_size"],
        random_state=SPLIT["random_state"],
        stratify=y,
    )
    return Xtr, Xte, ytr, yte


def _lstm_inputs(X: pd.DataFrame, scaler) -> np.ndarray:
    Xs = scaler.transform(X)
    return Xs.reshape((Xs.shape[0], Xs.shape[1], 1))


# Weights from app/models/ensemble.py — must stay in sync.
ENSEMBLE_WEIGHTS = {"decision_tree": 0.40, "xgboost": 0.35, "lstm": 0.25}


def _ensemble_predict(dt_proba: np.ndarray, xgb_proba: np.ndarray,
                      lstm_proba: np.ndarray) -> np.ndarray:
    """Weighted prob average across the three models."""
    combined = (
        ENSEMBLE_WEIGHTS["decision_tree"] * dt_proba
        + ENSEMBLE_WEIGHTS["xgboost"] * xgb_proba
        + ENSEMBLE_WEIGHTS["lstm"] * lstm_proba
    )
    return combined.argmax(axis=1)


def _per_model_metrics(name: str, y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    acc = accuracy_score(y_true, y_pred)
    cls_report = classification_report(
        y_true, y_pred,
        labels=list(range(4)),
        target_names=LABEL_NAMES,
        output_dict=True,
        zero_division=0,
    )
    cm = confusion_matrix(y_true, y_pred, labels=list(range(4)))
    return {
        "accuracy": float(acc),
        "per_class": {
            lbl: {k: float(v) for k, v in cls_report[lbl].items()}
            for lbl in LABEL_NAMES
        },
        "confusion_matrix": cm.tolist(),
        "macro_f1": float(cls_report["macro avg"]["f1-score"]),
        "weighted_f1": float(cls_report["weighted avg"]["f1-score"]),
    }


def _write_reports(results: dict, n_train: int, n_test: int):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    out_json = os.path.join(REPORTS_DIR, "accuracy_repro.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nWrote {out_json}")

    out_md = os.path.join(REPORTS_DIR, "accuracy_repro.md")
    lines = []
    lines.append("# Accuracy reproduction (Phase 2)\n")
    lines.append(f"_Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')}_  \n")
    lines.append(f"Dataset: `{DATASET_PATH}`  ")
    lines.append(f"Split: stratified 80/20 (seed={SPLIT['random_state']}), "
                 f"n_train={n_train:,}, n_test={n_test:,}  ")
    lines.append(f"Ensemble weights: DT {ENSEMBLE_WEIGHTS['decision_tree']} / "
                 f"XGB {ENSEMBLE_WEIGHTS['xgboost']} / LSTM {ENSEMBLE_WEIGHTS['lstm']}  \n")

    lines.append("## Headline accuracy vs. report\n")
    lines.append("| Model | Test accuracy | Report target | Δ |")
    lines.append("|---|---|---|---|")
    for name, m in results["models"].items():
        target = REPORT_TARGETS.get(name)
        if target is None:
            delta = "—"
        else:
            d = m["accuracy"] - target
            flag = "" if abs(d) <= LARGE_DELTA else "  ⚠"
            delta = f"{d:+.4f}{flag}"
        target_str = f"{target:.4f}" if target else "—"
        lines.append(f"| {name} | {m['accuracy']:.4f} | {target_str} | {delta} |")
    lines.append("")

    for name, m in results["models"].items():
        lines.append(f"## {name}\n")
        lines.append("| Class | Precision | Recall | F1 | Support |")
        lines.append("|---|---|---|---|---|")
        for cls in LABEL_NAMES:
            r = m["per_class"][cls]
            lines.append(
                f"| {cls} | {r['precision']:.4f} | {r['recall']:.4f} | "
                f"{r['f1-score']:.4f} | {int(r['support'])} |"
            )
        lines.append("")
        lines.append("**Confusion matrix** (rows = truth, cols = pred):\n")
        lines.append("|  | " + " | ".join(LABEL_NAMES) + " |")
        lines.append("|---|" + "|".join(["---"] * 4) + "|")
        for i, cls in enumerate(LABEL_NAMES):
            row = m["confusion_matrix"][i]
            lines.append(f"| {cls} | " + " | ".join(str(v) for v in row) + " |")
        lines.append("")
        lines.append(f"macro-F1: {m['macro_f1']:.4f}  ")
        lines.append(f"weighted-F1: {m['weighted_f1']:.4f}\n")

    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Wrote {out_md}")


def main() -> int:
    feature_names, scaler, dt, xgb, lstm, X, y = _load_inputs()

    print(f"\nSplit: stratified 80/20, random_state={SPLIT['random_state']}")
    Xtr, Xte, ytr, yte = _split(X, y)
    print(f"  train: {len(Xtr):,}   test: {len(Xte):,}")

    print("\nPredicting on test set...")
    print("  DT proba ...")
    dt_proba = dt.predict_proba(Xte)
    dt_pred = dt_proba.argmax(axis=1)
    print(f"    DT pred sample: {np.bincount(dt_pred, minlength=4).tolist()}")

    print("  XGB proba ...")
    xgb_proba = xgb.predict_proba(Xte)
    xgb_pred = xgb_proba.argmax(axis=1)
    print(f"    XGB pred sample: {np.bincount(xgb_pred, minlength=4).tolist()}")

    print("  LSTM proba ...")
    Xte_lstm = _lstm_inputs(Xte, scaler)
    lstm_proba = lstm.predict(Xte_lstm, batch_size=2048, verbose=0)
    lstm_pred = lstm_proba.argmax(axis=1)
    print(f"    LSTM pred sample: {np.bincount(lstm_pred, minlength=4).tolist()}")

    print("  Ensemble (weighted prob avg) ...")
    ens_pred = _ensemble_predict(dt_proba, xgb_proba, lstm_proba)
    print(f"    Ensemble pred sample: {np.bincount(ens_pred, minlength=4).tolist()}")

    y_true = yte.to_numpy()
    results = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "dataset_path": DATASET_PATH,
        "split": dict(SPLIT),
        "n_train": int(len(Xtr)),
        "n_test": int(len(Xte)),
        "ensemble_weights": ENSEMBLE_WEIGHTS,
        "report_targets": REPORT_TARGETS,
        "models": {
            "decision_tree": _per_model_metrics("decision_tree", y_true, dt_pred),
            "xgboost":       _per_model_metrics("xgboost", y_true, xgb_pred),
            "lstm":          _per_model_metrics("lstm", y_true, lstm_pred),
            "ensemble":      _per_model_metrics("ensemble", y_true, ens_pred),
        },
    }

    print("\nHeadline accuracy vs. report:")
    flagged = []
    for name, m in results["models"].items():
        target = REPORT_TARGETS.get(name)
        if target is None:
            print(f"  {name:<14s} acc={m['accuracy']:.4f}   "
                  f"macro-F1={m['macro_f1']:.4f}")
        else:
            delta = m["accuracy"] - target
            mark = "" if abs(delta) <= LARGE_DELTA else "  <-- FLAG"
            print(f"  {name:<14s} acc={m['accuracy']:.4f}   "
                  f"target={target:.4f}   delta={delta:+.4f}{mark}")
            if abs(delta) > LARGE_DELTA:
                flagged.append(name)

    _write_reports(results, len(Xtr), len(Xte))

    if flagged:
        print(f"\n[!] {len(flagged)} model(s) deviate >5pp from report: {flagged}")
        print("    Possible causes: different label encoding, different split,")
        print("    or the report's number was measured on a different CSV cut.")
        return 1
    print("\nAll models within 5pp of the report's headline accuracy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
