"""Retrain Decision Tree + XGBoost on the 4-class dataset.

Run from repo root with `data/dataset.csv` present:
    python -m app.models.training.train_models

Writes artifacts to `<MODEL_DIR>/` (default: repo `models/`).
"""
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import classification_report
from sklearn.utils.class_weight import compute_class_weight
from xgboost import XGBClassifier

from app.models._paths import model_dir

DATA_PATH = os.environ.get("DATASET_PATH", "data/dataset.csv")
MODEL_DIR = model_dir()
os.makedirs(MODEL_DIR, exist_ok=True)

print("[1/6] Loading dataset...")
df = pd.read_csv(DATA_PATH)

print("[2/6] Preparing features...")
DROP_COLS = ["url", "type", "label", "scan_date", "domain",
             "web_http_status", "web_is_live", "web_ext_ratio",
             "web_unique_domains", "web_favicon", "web_csp",
             "web_xframe", "web_hsts", "web_xcontent", "web_security_score",
             "web_forms_count", "web_password_fields", "web_hidden_inputs",
             "web_has_login", "web_ssl_valid",
             "https", "abnormal_url"]
X = df.drop(columns=[c for c in DROP_COLS if c in df.columns])
y = df["label"]
X = X.apply(pd.to_numeric, errors="coerce").fillna(0)

print(f"     Features: {X.shape[1]} | Samples: {X.shape[0]}")

print("[3/6] Computing class weights...")
classes = np.unique(y)
weights = compute_class_weight(class_weight="balanced", classes=classes, y=y)
class_weight_dict = {0: 1.0, 1: 1.5, 2: 2.0, 3: 3.0}
print(f"     Class weights: {class_weight_dict}")

print("[4/6] Splitting data...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"     Train: {X_train.shape[0]} | Test: {X_test.shape[0]}")

print("[5/6] Training Decision Tree...")
dt_model = DecisionTreeClassifier(
    max_depth=20,
    min_samples_split=10,
    class_weight={0: 1.0, 1: 1.5, 2: 2.0, 3: 3.0},
    random_state=42,
)
dt_model.fit(X_train, y_train)
dt_preds = dt_model.predict(X_test)

print("\n-- Decision Tree Results --")
print(classification_report(y_test, dt_preds,
      target_names=["benign", "defacement", "phishing", "malware"]))

dt_path = os.path.join(MODEL_DIR, "decision_tree.pkl")
joblib.dump(dt_model, dt_path)
print(f"     Saved -> {dt_path}")

print("\n[6/6] Training XGBoost...")
sample_weights = np.array([class_weight_dict[label] for label in y_train])

xgb_model = XGBClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    eval_metric="mlogloss",
    random_state=42,
    n_jobs=-1,
)
xgb_model.fit(X_train, y_train, sample_weight=sample_weights)
xgb_preds = xgb_model.predict(X_test)

print("\n-- XGBoost Results --")
print(classification_report(y_test, xgb_preds,
      target_names=["benign", "defacement", "phishing", "malware"]))

xgb_path = os.path.join(MODEL_DIR, "xgboost.pkl")
joblib.dump(xgb_model, xgb_path)
print(f"     Saved -> {xgb_path}")

feature_path = os.path.join(MODEL_DIR, "feature_names.pkl")
joblib.dump(X.columns.tolist(), feature_path)
print(f"\n     Feature names saved -> {feature_path}")

print("\nAll models retrained with class balancing.")
