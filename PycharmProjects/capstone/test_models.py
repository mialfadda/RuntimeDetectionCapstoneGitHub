import sys
sys.path.insert(0, '/Users/aljohara/PycharmProjects/capstone')
import joblib
import pandas as pd

# Load actual rows from the dataset instead of manually crafting features
df = pd.read_csv("data/dataset.csv")
DROP_COLS = ["url", "type", "label", "scan_date", "domain"]
feature_names = joblib.load("backend/app/models/saved/feature_names.pkl")

# Grab a real phishing row and a real benign row
phishing_row = df[df["type"] == "phishing"].iloc[0]
benign_row = df[df["type"] == "benign"].iloc[0]

phishing_features = {f: phishing_row.get(f, 0) for f in feature_names}
benign_features = {f: benign_row.get(f, 0) for f in feature_names}

print("Sample phishing URL:", df[df["type"] == "phishing"].iloc[0]["url"])
print("Sample benign URL:", df[df["type"] == "benign"].iloc[0]["url"])

from backend.app.models.decision_tree_model import DecisionTreeModel
from backend.app.models.xgboost_model import XGBoostModel
from backend.app.models.lstm_model import LSTMModel

dt = DecisionTreeModel()
xgb = XGBoostModel()
lstm = LSTMModel()

print("\n=== Phishing URL ===")
print("DT  :", dt.predict(phishing_features))
print("XGB :", xgb.predict(phishing_features))
print("LSTM:", lstm.predict(phishing_features))

print("\n=== Benign URL ===")
print("DT  :", dt.predict(benign_features))
print("XGB :", xgb.predict(benign_features))
print("LSTM:", lstm.predict(benign_features))