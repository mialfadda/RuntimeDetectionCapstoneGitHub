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
shap_result = shap_exp.explain(phishing_features)
print(shap_result)

print("\n" + "=" * 60)
print("LIME EXPLANATION")
print("=" * 60)
from backend.app.explainability.lime_explainer import LIMEExplainer
lime_exp = LIMEExplainer()
lime_result = lime_exp.explain(phishing_features)
print(lime_result)

print("\n" + "=" * 60)
print("LLM EXPLANATION")
print("=" * 60)
from backend.app.explainability.llm_explainer import LLMExplainer
llm_exp = LLMExplainer()

# Simulate a scan result to pass to LLM
scan_result = {
    "predicted_label": "phishing",
    "confidence": 0.74,
    "risk_level": "high"
}

llm_result = llm_exp.explain(
    url="http://br-icloud.com.br",
    scan_result=scan_result,
    shap_result=shap_result
)
print(llm_result)