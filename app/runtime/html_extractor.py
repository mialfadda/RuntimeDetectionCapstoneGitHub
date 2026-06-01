import re
from bs4 import BeautifulSoup


SUSPICIOUS_SCRIPT_PATTERNS = [
    "eval(", "unescape(", "atob(", "document.write(",
    "window.location", "iframe", "base64",
]


def extract_html_features(html: str) -> dict:
    """Extract HTML features. Returns an empty-ish dict for empty input."""
    if not html:
        return {}

    soup = BeautifulSoup(html, "html.parser")

    forms = soup.find_all("form")
    inputs = soup.find_all("input")
    has_password_field = any(
        i.get("type", "").lower() == "password" for i in inputs
    )

    all_links = soup.find_all("a", href=True)
    external_links = [a for a in all_links if a["href"].startswith("http")]

    scripts = soup.find_all("script")
    script_text = " ".join(s.get_text() for s in scripts)
    suspicious_script_count = sum(
        1 for pattern in SUSPICIOUS_SCRIPT_PATTERNS
        if pattern in script_text
    )

    hidden_elements = soup.find_all(
        style=re.compile(r"display\s*:\s*none|visibility\s*:\s*hidden")
    )

    iframes = soup.find_all("iframe")
    meta_tags = soup.find_all("meta")
    has_favicon = bool(soup.find("link", rel=re.compile("icon", re.I)))
    has_redirect_meta = bool(
        soup.find("meta", attrs={"http-equiv": re.compile("refresh", re.I)})
    )

    title = soup.find("title")
    title_length = len(title.get_text()) if title else 0

    return {
        "num_forms": len(forms),
        "num_inputs": len(inputs),
        "has_password_field": int(has_password_field),
        "num_external_links": len(external_links),
        "num_total_links": len(all_links),
        "num_scripts": len(scripts),
        "suspicious_script_count": suspicious_script_count,
        "num_iframes": len(iframes),
        "num_hidden_elements": len(hidden_elements),
        "num_meta_tags": len(meta_tags),
        "has_favicon": int(has_favicon),
        "has_redirect_meta": int(has_redirect_meta),
        "title_length": title_length,
    }
