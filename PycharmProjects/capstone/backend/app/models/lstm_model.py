import numpy as np
import joblib
from tensorflow.keras.models import load_model

MODEL_PATH = "backend/app/models/saved/lstm_model.keras"
SCALER_PATH = "backend/app/models/saved/scaler.pkl"
FEATURE_PATH = "backend/app/models/saved/feature_names.pkl"

LABEL_MAP = {0: "benign", 1: "defacement", 2: "phishing", 3: "malware"}


class LSTMModel:
    def __init__(self):
        self.model = load_model(MODEL_PATH)
        self.scaler = joblib.load(SCALER_PATH)
        self.feature_names = joblib.load(FEATURE_PATH)
        print("[LSTM] Model loaded.")

    def predict(self, feature_dict: dict) -> dict:
        # Align features
        import pandas as pd
        vector = pd.DataFrame([{f: feature_dict.get(f, 0) for f in self.feature_names}])
        vector_scaled = self.scaler.transform(vector)

        # Scale then reshape for LSTM
        vector_scaled = self.scaler.transform(vector)
        vector_lstm = vector_scaled.reshape((1, vector_scaled.shape[1], 1))

        probabilities = self.model.predict(vector_lstm, verbose=0)[0]
        prediction = int(np.argmax(probabilities))

        return {
            "model": "lstm",
            "predicted_class": prediction,
            "predicted_label": LABEL_MAP[prediction],
            "confidence": round(float(probabilities[prediction]), 4),
            "probabilities": {
                LABEL_MAP[i]: round(float(p), 4)
                for i, p in enumerate(probabilities)
            }
        }