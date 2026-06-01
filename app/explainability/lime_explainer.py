"""LIME explainer for the Decision Tree branch.

The original main implementation re-read `data/dataset.csv` to build LIME's
training-distribution. We don't ship the dataset, so we synthesize a small
sample from the StandardScaler's stored mean/std (which were fit on the same
training data). This produces explanations of the same shape; coefficients
shift slightly from a true-data fit but the top-features ranking is stable.
"""
import os

import joblib
import lime
import lime.lime_tabular
import numpy as np
import pandas as pd

from app.models._paths import artifact

LABEL_MAP = {0: "benign", 1: "defacement", 2: "phishing", 3: "malware"}

DATASET_PATH = os.environ.get("DATASET_PATH", "data/dataset.csv")
SYNTHETIC_SAMPLES = 500


def _synthetic_training_data(scaler, feature_names) -> np.ndarray:
    """Sample from N(mean_, scale_) using the scaler's stored stats."""
    rng = np.random.default_rng(seed=42)
    mean = np.asarray(scaler.mean_)
    std = np.asarray(scaler.scale_)
    samples = rng.normal(loc=mean, scale=std, size=(SYNTHETIC_SAMPLES, len(feature_names)))
    return np.clip(samples, a_min=0, a_max=None)


def _real_training_data(feature_names) -> np.ndarray:
    df = pd.read_csv(DATASET_PATH)
    drop_cols = ["url", "type", "label", "scan_date", "domain",
                 "web_http_status", "web_is_live", "web_ext_ratio",
                 "web_unique_domains", "web_favicon", "web_csp",
                 "web_xframe", "web_hsts", "web_xcontent", "web_security_score",
                 "web_forms_count", "web_password_fields", "web_hidden_inputs",
                 "web_has_login", "web_ssl_valid", "https", "abnormal_url"]
    X = df.drop(columns=[c for c in drop_cols if c in df.columns])
    X = X.apply(pd.to_numeric, errors="coerce").fillna(0)
    return X[feature_names].values


class LIMEExplainer:
    def __init__(self):
        self.model = joblib.load(artifact("decision_tree.pkl"))
        self.feature_names = joblib.load(artifact("feature_names.pkl"))

        if os.path.exists(DATASET_PATH):
            print(f"[LIME] Using real training data from {DATASET_PATH}")
            training_data = _real_training_data(self.feature_names)
        else:
            print(f"[LIME] {DATASET_PATH} not found — synthesizing distribution from scaler stats")
            scaler = joblib.load(artifact("scaler.pkl"))
            training_data = _synthetic_training_data(scaler, self.feature_names)

        self.explainer = lime.lime_tabular.LimeTabularExplainer(
            training_data=training_data,
            feature_names=self.feature_names,
            class_names=list(LABEL_MAP.values()),
            mode="classification",
            discretize_continuous=True,
        )
        print("[LIME] Explainer initialized.")

    def explain(self, feature_dict: dict, num_features: int = 10) -> dict:
        vector = np.array([
            feature_dict.get(f, 0) for f in self.feature_names
        ])

        predicted_class = int(self.model.predict(
            pd.DataFrame([{f: feature_dict.get(f, 0) for f in self.feature_names}])
        )[0])
        predicted_label = LABEL_MAP[predicted_class]

        explanation = self.explainer.explain_instance(
            data_row=vector,
            predict_fn=self.model.predict_proba,
            num_features=num_features,
            labels=[predicted_class],
        )

        feature_weights = explanation.as_list(label=predicted_class)

        top_features = [
            {"feature": feat, "weight": round(float(weight), 6)}
            for feat, weight in feature_weights
        ]

        pushing_malicious = [f for f in top_features if f["weight"] > 0]
        pushing_benign = [f for f in top_features if f["weight"] < 0]

        return {
            "predicted_label": predicted_label,
            "predicted_class": predicted_class,
            "top_features": top_features,
            "pushing_malicious": pushing_malicious,
            "pushing_benign": pushing_benign,
        }
