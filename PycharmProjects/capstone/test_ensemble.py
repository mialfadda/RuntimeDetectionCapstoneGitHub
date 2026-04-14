import sys
sys.path.insert(0, '/Users/aljohara/PycharmProjects/capstone')
import joblib
import pandas as pd

df = pd.read_csv("data/dataset.csv")
feature_names = joblib.load("backend/app/models/saved/feature_names.pkl")

phishing_row = df[df["type"] == "phishing"].iloc[0]
benign_row = df[df["type"] == "benign"].iloc[0]
malware_row = df[df["type"] == "malware"].iloc[0]

phishing_features = {f: phishing_row.get(f, 0) for f in feature_names}
benign_features = {f: benign_row.get(f, 0) for f in feature_names}
malware_features = {f: malware_row.get(f, 0) for f in feature_names}

from backend.app.models.ensemble import EnsembleModel
ensemble = EnsembleModel()

print("\n=== Phishing URL:", df[df["type"] == "phishing"].iloc[0]["url"], "===")
print(ensemble.predict(phishing_features))

print("\n=== Benign URL:", df[df["type"] == "benign"].iloc[0]["url"], "===")
print(ensemble.predict(benign_features))

print("\n=== Malware URL:", df[df["type"] == "malware"].iloc[0]["url"], "===")
print(ensemble.predict(malware_features))