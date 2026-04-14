import sys
sys.path.insert(0, '/Users/aljohara/PycharmProjects/capstone')
import pandas as pd
import joblib

df = pd.read_csv("data/dataset.csv")
feature_names = joblib.load("backend/app/models/saved/feature_names.pkl")

phishing_row = df[df["type"] == "phishing"].iloc[0]
phishing_features = {f: phishing_row.get(f, 0) for f in feature_names}

print("=" * 60)
print("SHAP EXPLANATION")
print("=" * 60)
from backend.app.explainability.shap_explainer import SHAPExplainer
shap_exp = SHAPExplainer()
print(shap_exp.explain(phishing_features))

print("\n" + "=" * 60)
print("LIME EXPLANATION")
print("=" * 60)
from backend.app.explainability.lime_explainer import LIMEExplainer
lime_exp = LIMEExplainer()
print(lime_exp.explain(phishing_features))