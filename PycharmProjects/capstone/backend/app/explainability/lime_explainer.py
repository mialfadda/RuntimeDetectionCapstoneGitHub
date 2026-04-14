import lime
import lime.lime_tabular
import joblib
import numpy as np
import pandas as pd

MODEL_PATH = "backend/app/models/saved/decision_tree.pkl"
FEATURE_PATH = "backend/app/models/saved/feature_names.pkl"
DATA_PATH = "data/dataset.csv"

LABEL_MAP = {0: "benign", 1: "defacement", 2: "phishing", 3: "malware"}


class LIMEExplainer:
    def __init__(self):
        self.model = joblib.load(MODEL_PATH)
        self.feature_names = joblib.load(FEATURE_PATH)

        # LIME needs training data distribution to generate perturbations
        print("[LIME] Loading training data for distribution...")
        df = pd.read_csv(DATA_PATH)
        DROP_COLS = ["url", "type", "label", "scan_date", "domain",
                     "web_http_status", "web_is_live", "web_ext_ratio",
                     "web_unique_domains", "web_favicon", "web_csp",
                     "web_xframe", "web_hsts", "web_xcontent", "web_security_score",
                     "web_forms_count", "web_password_fields", "web_hidden_inputs",
                     "web_has_login", "web_ssl_valid", "https", "abnormal_url"]
        X = df.drop(columns=[c for c in DROP_COLS if c in df.columns])
        X = X.apply(pd.to_numeric, errors="coerce").fillna(0)

        self.explainer = lime.lime_tabular.LimeTabularExplainer(
            training_data=X.values,
            feature_names=self.feature_names,
            class_names=list(LABEL_MAP.values()),
            mode="classification",
            discretize_continuous=True,
        )
        print("[LIME] Explainer initialized.")

    def explain(self, feature_dict: dict, num_features: int = 10) -> dict:
        """
        Generates a LIME explanation for a single prediction.
        Returns top influential features with their weights.
        """
        vector = np.array([
            feature_dict.get(f, 0) for f in self.feature_names
        ])

        # Get predicted class
        import pandas as pd
        predicted_class = int(self.model.predict(
            pd.DataFrame([{f: feature_dict.get(f, 0) for f in self.feature_names}])
        )[0])
        predicted_label = LABEL_MAP[predicted_class]

        # Generate LIME explanation
        explanation = self.explainer.explain_instance(
            data_row=vector,
            predict_fn=self.model.predict_proba,
            num_features=num_features,
            labels=[predicted_class],
        )

        # Extract feature weights for predicted class
        feature_weights = explanation.as_list(label=predicted_class)

        # Format results
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