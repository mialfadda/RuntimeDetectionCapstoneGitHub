"""LLM-based natural-language summary of a scan.

Uses OpenAI when `OPENAI_API_KEY` is set; falls back to a template-based
summary otherwise so the app keeps working in dev / offline.
"""
import json
import os
from typing import Optional


LABEL_DESCRIPTIONS = {
    "benign": "a safe, legitimate website",
    "phishing": "a phishing site designed to steal credentials or personal information",
    "defacement": "a defaced website that has been compromised and altered by attackers",
    "malware": "a malware-distributing site that may install malicious software",
}


def _action_for(label: str, confidence: float) -> str:
    if label == "benign":
        return "safe_to_visit"
    if label == "phishing" and confidence > 0.8:
        return "avoid"
    if label == "malware":
        return "avoid"
    return "proceed_with_caution"


def _template_summary(url: str, label: str, confidence: float, top_features: list) -> str:
    desc = LABEL_DESCRIPTIONS.get(label, "an unrecognized category")
    pct = round(confidence * 100, 1)
    if label == "benign":
        return (
            f"{url} appears to be {desc} (confidence {pct}%). "
            "No major risk indicators were detected. Always remain alert for "
            "unexpected login prompts or downloads."
        )
    drivers = ", ".join(f.get("feature", "") for f in top_features[:3] if f.get("feature"))
    action = "Do not enter credentials or download files" if label in ("phishing", "malware") else "Exercise caution"
    return (
        f"{url} was classified as {desc} (confidence {pct}%). "
        f"Top contributing signals: {drivers or 'URL structure heuristics'}. "
        f"{action}; verify the URL before interacting with this page."
    )


class LLMExplainer:
    def __init__(self):
        self.api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
        self.client = None
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                print("[LLM] OpenAI client initialized.")
            except Exception as e:
                print(f"[LLM] OpenAI unavailable ({e}); falling back to template summaries.")
                self.client = None
        else:
            print("[LLM] OPENAI_API_KEY not set — using template summaries.")

    def explain(self, url: str, scan_result: dict, shap_result: dict) -> dict:
        def clean(text: str) -> str:
            return str(text).encode("ascii", "ignore").decode()

        predicted_label = scan_result.get("predicted_label", "unknown")
        confidence = float(scan_result.get("confidence", 0) or 0)
        top_features = shap_result.get("top_features", [])[:5]
        pushing_malicious = shap_result.get("pushing_malicious", [])
        pushing_benign = shap_result.get("pushing_benign", [])

        if self.client is None:
            explanation_text = _template_summary(url, predicted_label, confidence, top_features)
        else:
            prompt = f"""
You are a cybersecurity assistant explaining website scan results to a non-technical user.

A URL was scanned and classified as:
{predicted_label} ({LABEL_DESCRIPTIONS.get(predicted_label, "unknown")})

Confidence: {round(confidence * 100, 1)}%
URL: {url}

Top features that influenced this decision:
{json.dumps(top_features, indent=2)}

Features pushing toward malicious:
{[f.get('feature') for f in pushing_malicious]}

Features pushing toward benign:
{[f.get('feature') for f in pushing_benign]}

Write a short, clear explanation (3-4 sentences) for a non-technical user that:
1. States what the scan found
2. Explains the main suspicious signals in plain English
3. Gives a recommended action (proceed with caution / avoid / safe to visit)

Do not use technical jargon. Be direct and helpful.
"""
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4.1-mini",
                    messages=[{"role": "user", "content": clean(prompt)}],
                    max_tokens=300,
                )
                explanation_text = response.choices[0].message.content
            except Exception as e:
                print(f"[LLM] OpenAI call failed ({e}); using template fallback.")
                explanation_text = _template_summary(url, predicted_label, confidence, top_features)

        return {
            "url": url,
            "predicted_label": predicted_label,
            "confidence_pct": round(confidence * 100, 1),
            "explanation": explanation_text,
            "recommended_action": _action_for(predicted_label, confidence),
        }
