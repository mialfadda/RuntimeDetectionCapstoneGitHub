from backend.app.models.decision_tree_model import DecisionTreeModel
from backend.app.models.xgboost_model import XGBoostModel
from backend.app.models.lstm_model import LSTMModel

LABEL_MAP = {0: "benign", 1: "defacement", 2: "phishing", 3: "malware"}

# Weights based on each model's phishing recall performance
MODEL_WEIGHTS = {
    "decision_tree": 0.40,
    "xgboost": 0.35,
    "lstm": 0.25
}


class EnsembleModel:
    def __init__(self):
        self.dt = DecisionTreeModel()
        self.xgb = XGBoostModel()
        self.lstm = LSTMModel()
        print("[Ensemble] All models loaded.")

    def predict(self, feature_dict: dict) -> dict:
        # Get predictions from all three models
        dt_result = self.dt.predict(feature_dict)
        xgb_result = self.xgb.predict(feature_dict)
        lstm_result = self.lstm.predict(feature_dict)

        results = [dt_result, xgb_result, lstm_result]

        # Weighted average of probabilities
        final_probs = {label: 0.0 for label in LABEL_MAP.values()}

        for result in results:
            weight = MODEL_WEIGHTS[result["model"]]
            for label, prob in result["probabilities"].items():
                final_probs[label] += prob * weight

        # Final prediction is the class with highest weighted probability
        final_label = max(final_probs, key=final_probs.get)
        final_class = [k for k, v in LABEL_MAP.items() if v == final_label][0]
        confidence = round(final_probs[final_label], 4)

        # Determine risk level
        if final_label == "benign":
            risk_level = "low"
        elif final_label == "defacement":
            risk_level = "medium"
        elif final_label == "phishing":
            risk_level = "high"
        else:  # malware
            risk_level = "critical"

        return {
            "predicted_class": final_class,
            "predicted_label": final_label,
            "confidence": confidence,
            "risk_level": risk_level,
            "final_probabilities": {k: round(v, 4) for k, v in final_probs.items()},
            "model_contributions": {
                "decision_tree": dt_result["predicted_label"],
                "xgboost": xgb_result["predicted_label"],
                "lstm": lstm_result["predicted_label"],
            }
        }