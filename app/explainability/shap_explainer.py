import joblib
import numpy as np
import pandas as pd
import shap

from app.models._paths import artifact

LABEL_MAP = {0: "benign", 1: "defacement", 2: "phishing", 3: "malware"}


class SHAPExplainer:
    def __init__(self):
        self.model = joblib.load(artifact("decision_tree.pkl"))
        self.feature_names = joblib.load(artifact("feature_names.pkl"))
        self.explainer = shap.TreeExplainer(self.model)
        print("[SHAP] Explainer initialized.")

    def explain(self, feature_dict: dict) -> dict:
        vector = pd.DataFrame([{
            f: feature_dict.get(f, 0) for f in self.feature_names
        }])

        shap_values = self.explainer.shap_values(vector)

        predicted_class = int(self.model.predict(vector)[0])
        predicted_label = LABEL_MAP[predicted_class]

        # shap_values shape depends on classifier output — handle both
        # multi-class (list per class) and 3-D array layouts.
        sv = np.asarray(shap_values)
        if sv.ndim == 3:
            class_shap = sv[predicted_class][0]
        elif isinstance(shap_values, list):
            class_shap = np.asarray(shap_values[predicted_class][0])
        else:
            class_shap = sv[0]

        feature_impacts = [
            {"feature": name, "shap_value": round(float(val), 6)}
            for name, val in zip(self.feature_names, class_shap)
        ]
        feature_impacts.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
        top_features = feature_impacts[:10]

        pushing_malicious = [f for f in top_features if f["shap_value"] > 0]
        pushing_benign = [f for f in top_features if f["shap_value"] < 0]

        expected = self.explainer.expected_value
        if isinstance(expected, (list, np.ndarray)):
            base_value = float(np.asarray(expected).flatten()[predicted_class])
        else:
            base_value = float(expected)

        return {
            "predicted_label": predicted_label,
            "predicted_class": predicted_class,
            "top_features": top_features,
            "pushing_malicious": pushing_malicious,
            "pushing_benign": pushing_benign,
            "base_value": round(base_value, 6),
        }
