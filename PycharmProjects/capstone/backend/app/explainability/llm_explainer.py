from openai import OpenAI
import os
import json

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

LABEL_DESCRIPTIONS = {
    "benign": "a safe, legitimate website",
    "phishing": "a phishing site designed to steal credentials or personal information",
    "defacement": "a defaced website that has been compromised and altered by attackers",
    "malware": "a malware-distributing site that may install malicious software",
}


class LLMExplainer:
    def __init__(self):
        print("[LLM] Explainer initialized.")

    def explain(self, url: str, scan_result: dict, shap_result: dict) -> dict:

        def clean(text):
            return str(text).encode('ascii', 'ignore').decode()

        predicted_label = scan_result.get("predicted_label", "unknown")
        confidence = scan_result.get("confidence", 0)

        top_features = shap_result.get("top_features", [])[:5]
        pushing_malicious = shap_result.get("pushing_malicious", [])
        pushing_benign = shap_result.get("pushing_benign", [])

        prompt = f"""
You are a cybersecurity assistant explaining website scan results to a non-technical user.

A URL was scanned and classified as:
{predicted_label} ({LABEL_DESCRIPTIONS.get(predicted_label, "unknown")})

Confidence: {round(confidence * 100, 1)}%
URL: {url}

Top features that influenced this decision:
{json.dumps(top_features, indent=2)}

Features pushing toward malicious:
{[f['feature'] for f in pushing_malicious]}

Features pushing toward benign:
{[f['feature'] for f in pushing_benign]}

Write a short, clear explanation (3-4 sentences) for a non-technical user that:
1. States what the scan found
2. Explains the main suspicious signals in plain English
3. Gives a recommended action (proceed with caution / avoid / safe to visit)

Do not use technical jargon. Be direct and helpful.
"""

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "user",
                    "content": clean(prompt)
                }
            ],
            max_tokens=300
        )

        explanation_text = response.choices[0].message.content

        return {
            "url": url,
            "predicted_label": predicted_label,
            "confidence_pct": round(confidence * 100, 1),
            "explanation": explanation_text,
            "recommended_action": self._get_action(
                predicted_label,
                confidence
            ),
        }

    def _get_action(self, label: str, confidence: float) -> str:

        if label == "benign":
            return "safe_to_visit"

        elif label == "phishing" and confidence > 0.8:
            return "avoid"

        elif label == "malware":
            return "avoid"

        else:
            return "proceed_with_caution"