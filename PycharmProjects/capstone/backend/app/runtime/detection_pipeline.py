import uuid
import requests

from backend.app.interfaces.contracts import (
    ScanRequest, ScanResult, FeatureVector, ModelContributions
)
from backend.app.runtime.url_extractor import extract_url_features
from backend.app.runtime.html_extractor import extract_html_features
from backend.app.runtime.runtime_monitor import extract_runtime_features
from backend.app.models.ensemble import EnsembleModel

# Load ensemble once at startup
ensemble = EnsembleModel()


def fetch_page(url: str) -> tuple:
    """Returns (html_text, status_code)"""
    try:
        if not url.startswith("http"):
            url = "http://" + url
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, timeout=5, headers=headers)
        return response.text, response.status_code
    except Exception as e:
        print(f"[Pipeline] Could not fetch page for {url}: {e}")
        return "", 0


def run_detection(request: ScanRequest) -> ScanResult:
    scan_id = request.scan_id or str(uuid.uuid4())

    try:
        # Step 1: URL features
        print(f"[Pipeline] Extracting URL features for: {request.url}")
        url_features = extract_url_features(request.url)

        # Step 2: Fetch page and extract HTML features
        print(f"[Pipeline] Fetching HTML...")
        html, status_code = fetch_page(request.url)
        html_features = extract_html_features(html) if html else {}

        # Step 3: Runtime features
        runtime_features = {}
        if request.runtime_evidence:
            print(f"[Pipeline] Extracting runtime features...")
            runtime_features = extract_runtime_features(request.runtime_evidence)

        # Step 4: Build feature dict — only URL-based features the models were trained on
        feature_dict = {
            "url_len": url_features.get("url_length", 0),
            "@": url_features.get("has_at_symbol", 0),
            "?": 1 if "?" in request.url else 0,
            "-": url_features.get("num_hyphens", 0),
            "=": 1 if "=" in request.url else 0,
            ".": url_features.get("num_dots", 0),
            "#": 1 if "#" in request.url else 0,
            "%": 1 if "%" in request.url else 0,
            "+": 1 if "+" in request.url else 0,
            "$": 1 if "$" in request.url else 0,
            "!": 1 if "!" in request.url else 0,
            "*": 1 if "*" in request.url else 0,
            ",": 1 if "," in request.url else 0,
            "//": url_features.get("has_double_slash_redirect", 0),
            "digits": url_features.get("num_digits_in_url", 0),
            "letters": sum(c.isalpha() for c in request.url),
            "Shortining_Service": url_features.get("is_url_shortener", 0),
            "having_ip_address": url_features.get("has_ip_address", 0),
            "phish_urgency_words": url_features.get("has_suspicious_keywords", 0),
            "phish_security_words": url_features.get("has_suspicious_keywords", 0),
            "phish_brand_mentions": 0,
            "phish_brand_hijack": 0,
            "phish_multiple_subdomains": int(url_features.get("subdomain_count", 0) > 2),
            "phish_long_path": int(url_features.get("path_depth", 0) > 4),
            "phish_many_params": int("?" in request.url and
                                     request.url.count("=") > 2),
            "phish_suspicious_tld": 0,
            "phish_adv_exact_brand_match": 0,
            "phish_adv_brand_in_subdomain": 0,
            "phish_adv_brand_in_path": 0,
            "phish_adv_hyphen_count": url_features.get("num_hyphens", 0),
            "phish_adv_number_count": url_features.get("num_digits_in_url", 0),
            "phish_adv_suspicious_tld": 0,
            "phish_adv_long_domain": int(url_features.get("domain_length", 0) > 20),
            "phish_adv_many_subdomains": int(url_features.get("subdomain_count", 0) > 2),
            "phish_adv_encoded_chars": int("%" in request.url),
            "phish_adv_path_keywords": url_features.get("has_suspicious_keywords", 0),
            "phish_adv_has_redirect": html_features.get("has_redirect_meta", 0),
            "phish_adv_many_params": int(request.url.count("=") > 2),
            "path_has_hacked_terms": 0,
            "suspicious_extension": int(request.url.endswith(
                (".exe", ".zip", ".php", ".js", ".bat"))),
            "path_underscore_count": request.url.count("_"),
            "is_gov_edu": int(request.url.endswith((".gov", ".edu"))),
        }

        # Step 5: Build FeatureVector for logging/contracts
        feature_vector = FeatureVector(
            url_length=url_features.get("url_length", 0),
            subdomain_count=url_features.get("subdomain_count", 0),
            path_depth=url_features.get("path_depth", 0),
            has_ip_address=url_features.get("has_ip_address", 0),
            is_https=url_features.get("is_https", 0),
            num_forms=html_features.get("num_forms", 0),
            has_password_field=html_features.get("has_password_field", 0),
            suspicious_script_count=html_features.get("suspicious_script_count", 0),
            suspicious_api_call_count=runtime_features.get("suspicious_api_call_count", 0),
            dom_mutation_count=runtime_features.get("dom_mutation_count", 0),
        )

        # Step 6: Run ensemble prediction
        print(f"[Pipeline] Running ensemble prediction...")
        ensemble_result = ensemble.predict(feature_dict)

        # Step 7: Return ScanResult
        return ScanResult(
            scan_id=scan_id,
            url=request.url,
            predicted_label=ensemble_result["predicted_label"],
            predicted_class=ensemble_result["predicted_class"],
            confidence=ensemble_result["confidence"],
            risk_level=ensemble_result["risk_level"],
            final_probabilities=ensemble_result["final_probabilities"],
            model_contributions=ModelContributions(
                **ensemble_result["model_contributions"]
            ),
            feature_vector=feature_vector,
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[Pipeline] Error during detection: {e}")
        return ScanResult(
            scan_id=scan_id,
            url=request.url,
            predicted_label="unknown",
            predicted_class=-1,
            confidence=0.0,
            risk_level="unknown",
            error=str(e)
        )