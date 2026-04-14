import joblib
import numpy as np

MODEL_PATH = "backend/app/models/saved/xgboost.pkl"
FEATURE_PATH = "backend/app/models/saved/feature_names.pkl"

LABEL_MAP = {0: "benign", 1: "defacement", 2: "phishing", 3: "malware"}


class XGBoostModel:
    def __init__(self):
        self.model = joblib.load(MODEL_PATH)
        self.feature_names = joblib.load(FEATURE_PATH)
        print("[XGBoost] Model loaded.")

    def predict(self, feature_dict: dict) -> dict:
        import pandas as pd
        vector = pd.DataFrame([{f: feature_dict.get(f, 0) for f in self.feature_names}])

        prediction = self.model.predict(vector)[0]
        probabilities = self.model.predict_proba(vector)[0]

        return {
            "model": "xgboost",
            "predicted_class": int(prediction),
            "predicted_label": LABEL_MAP[int(prediction)],
            "confidence": round(float(probabilities[prediction]), 4),
            "probabilities": {
                LABEL_MAP[i]: round(float(p), 4)
                for i, p in enumerate(probabilities)
            }
        }