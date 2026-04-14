import re
from urllib.parse import urlparse
import tldextract

# List of known URL shortener domains
URL_SHORTENERS = ["bit", "tinyurl", "t", "goo", "ow", "is", "buff", "shorturl"]

# Keywords commonly found in phishing URLs
SUSPICIOUS_KEYWORDS = [
    "login", "verify", "secure", "account", "update",
    "banking", "confirm", "password", "credential", "signin"
]


def extract_url_features(url: str) -> dict:
    """
    Extracts numerical and categorical features from a URL string.
    Returns a flat dictionary of features to be used in the FeatureVector.
    """
    parsed = urlparse(url)
    ext = tldextract.extract(url)

    return {
        "url_length": len(url),
        "subdomain_count": len(ext.subdomain.split(".")) if ext.subdomain else 0,
        "path_depth": len([p for p in parsed.path.split("/") if p]),
        "special_char_count": len(re.findall(r"[@!$&?%#=_~]", url)),
        "has_ip_address": int(bool(re.match(r"\d+\.\d+\.\d+\.\d+", parsed.netloc))),
        "tld": ext.suffix,
        "is_url_shortener": int(ext.domain in URL_SHORTENERS),
        "has_suspicious_keywords": int(
            any(kw in url.lower() for kw in SUSPICIOUS_KEYWORDS)
        ),
        "is_https": int(parsed.scheme == "https"),
        "num_digits_in_url": sum(c.isdigit() for c in url),
        "num_dots": url.count("."),
        "num_hyphens": url.count("-"),
        "has_at_symbol": int("@" in url),
        "has_double_slash_redirect": int("//" in parsed.path),
        "domain_length": len(ext.domain),
    }