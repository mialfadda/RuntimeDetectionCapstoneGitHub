import shap
import joblib
import numpy as np
import pandas as pd

MODEL_PATH = "backend/app/models/saved/decision_tree.pkl"
FEATURE_PATH = "backend/app/models/saved/feature_names.pkl"

LABEL_MAP = {0: "benign", 1: "defacement", 2: "phishing", 3: "malware"}


class SHAPExplainer:
    def __init__(self):
        self.model = joblib.load(MODEL_PATH)
        self.feature_names = joblib.load(FEATURE_PATH)
        self.explainer = shap.TreeExplainer(self.model)
        print("[SHAP] Explainer initialized.")

    def explain(self, feature_dict: dict) -> dict:
        """
        Computes SHAP values for a single prediction.
        Returns top contributing features and their impact.
        """
        # Build input vector
        vector = pd.DataFrame([{
            f: feature_dict.get(f, 0) for f in self.feature_names
        }])

        # Compute SHAP values — shape: (num_classes, num_features)
        shap_values = self.explainer.shap_values(vector)

        # Get predicted class
        import pandas as pd
        predicted_class = int(self.model.predict(
            pd.DataFrame([{f: feature_dict.get(f, 0) for f in self.feature_names}])
        )[0])
        predicted_label = LABEL_MAP[predicted_class]

        # Get SHAP values for the predicted class
        class_shap = np.array(shap_values[predicted_class][0])

        # Pair feature names with their SHAP values
        feature_impacts = [
            {"feature": name, "shap_value": round(float(val), 6)}
            for name, val in zip(self.feature_names, class_shap)
        ]

        # Sort by absolute impact
        feature_impacts.sort(key=lambda x: abs(x["shap_value"]), reverse=True)

        # Top 10 most influential features
        top_features = feature_impacts[:10]

        # Separate into pushing-toward and pushing-away
        pushing_malicious = [f for f in top_features if f["shap_value"] > 0]
        pushing_benign = [f for f in top_features if f["shap_value"] < 0]

        return {
            "predicted_label": predicted_label,
            "predicted_class": predicted_class,
            "top_features": top_features,
            "pushing_malicious": pushing_malicious,
            "pushing_benign": pushing_benign,
            "base_value": round(float(self.explainer.expected_value[predicted_class]), 6),
        }