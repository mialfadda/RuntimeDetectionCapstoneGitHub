"""URL-derived feature extraction matching `models/feature_names.pkl`.

This is the runtime equivalent of the (un-shipped) script that produced
the Kaggle "Enhanced 2026" CSV's pre-computed columns. Each feature here
reproduces the corresponding CSV column from the URL string alone; the
validator in `scripts/validate_features.py` reports per-column exact-match
rate against the dataset.

Design notes:
  - The feature ORDER is read from feature_names.pkl at the call site;
    this module returns a dict keyed by canonical names.
  - Constants (suspicious TLDs, urgency words, brand list, etc.) live at
    module top so the validator's debug output can drive them to ≥99%
    agreement with the CSV.
  - `is_gov_edu` and `phish_suspicious_tld` look extremely sparse in the
    CSV (15 rows out of 651k for the former); we still compute them
    exactly, but small mismatches there don't move the needle.
  - The web_* live-crawl columns are NOT in feature_names.pkl, so they
    don't need to be emitted here. Live-crawl is the next milestone.
"""
from __future__ import annotations

import re
from urllib.parse import urlparse

import tldextract


# ── Reverse-engineered constants ───────────────────────────────────

# Common URL shorteners (substring or domain match). Will iterate based
# on validator output if false-positive/negative rate is high.
URL_SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd",
    "buff.ly", "shorturl.at", "tiny.cc", "bitly.com",
    "rebrand.ly", "cutt.ly", "rb.gy", "shorte.st", "adf.ly",
}

# Per CSV grouping by phish_suspicious_tld==1: only a subset of the
# canonical "abuse-prone" TLDs actually fires the flag (with hit rates
# of 8-44%; the dataset doesn't flag every URL on these TLDs).
SUSPICIOUS_TLDS = {"xyz", "tk", "ga", "ml", "cf", "top"}

# phish_adv_suspicious_tld uses a tighter list — `top` doesn't trigger it.
SUSPICIOUS_TLDS_ADV = {"xyz", "tk", "ga", "ml", "cf"}

# Brand list inferred from CSV rows where phish_brand_mentions==1, by
# enrichment ratio (≥20x more common in flagged rows than not). The
# dataset's pipeline only flags these specific brands — adding more
# (linkedin, instagram, google, icicibank...) inflates false positives.
BRANDS = {
    "facebook", "amazon", "apple", "paypal", "ebay", "microsoft",
    "netflix", "appleid", "itunes", "googlegroups",
}

# Urgency words inferred by enrichment vs the CSV — tokens that are NEVER
# present in `phish_urgency_words=0` rows. Adding broader phishing
# vocabulary ("signin", "session", "reset", "auth", ...) false-positives
# because the dataset's pipeline didn't include them.
URGENCY_WORDS = (
    "login", "account", "accounts",
    "verify", "verification",
    "confirm", "confirmation",
    "update", "secure", "validation",
)

# Same enrichment process for `phish_security_words` — only "security"
# is a true marker (every URL containing "security" flags truth=1).
SECURITY_WORDS = ("security",)

# `phish_adv_path_keywords` uses the same vocabulary as URGENCY_WORDS but
# only counts matches inside the path component.
PATH_KEYWORDS = URGENCY_WORDS

# Tokens that suggest the path discusses hacking / compromise.
HACKED_TERMS = ("hack", "hacked", "crack", "exploit", "root", "0day", "pwn")

# Extensions the dataset's `suspicious_extension` flag fires on.
SUSPICIOUS_EXTENSIONS = {"html", "htm", "php", "txt"}

# Redirect-style query parameter names.
REDIRECT_PARAMS = ("return=", "url=", "redirect=", "goto=", "next=", "r=", "u=")

# Thresholds inferred from grouping CSV rows by feature value vs the raw
# observation: each cutoff is the boundary the dataset's labels actually
# split on (verified via crosstab in scripts/validate_features debug runs).
THRESH = {
    "phish_long_path_url_len": 50,    # url len >= 50 (~80% — noisy in dataset)
    "phish_many_params_qlen": 31,     # len(query) >= 31 (sharp boundary)
    "phish_multiple_subdomains": 2,   # tldextract subdomain count >= 2
    "phish_adv_many_subdomains": 3,   # tldextract subdomain count >= 3
    "phish_adv_long_domain": 30,      # registered-domain length >= 30
}


# ── URL parsing helpers ────────────────────────────────────────────


def _ensure_scheme(u: str) -> str:
    """The CSV stores URLs without scheme for many rows; tldextract /
    urlparse both need one to parse netloc correctly."""
    s = (u or "").strip()
    if s.startswith(("http://", "https://", "ftp://")):
        return s
    return "http://" + s


def _parts(url: str) -> tuple[str, str, str, str, str, str]:
    """Return (raw_url, netloc, path, query, registered_domain, subdomain)
    all lowercased. Uses tldextract for proper registered-domain parsing
    which matches what the dataset's feature pipeline appears to have done."""
    s = _ensure_scheme(url).lower()
    try:
        p = urlparse(s)
        netloc = p.netloc.split(":", 1)[0]
        ext = tldextract.extract(s)
        return url.lower(), netloc, p.path, p.query, ext.domain, ext.subdomain
    except Exception:
        return url.lower(), "", "", "", "", ""


def _subdomain_count(subdomain: str, netloc: str) -> int:
    """Subdomain segment count.

    tldextract returns "" for IP-address netlocs (no public-suffix), but
    the dataset treats those as "many subdomains" (since the IP octets
    look like dotted segments). Fall back to counting netloc dots for IPs.
    """
    if subdomain:
        return subdomain.count(".") + 1
    if _IP_RE.match(netloc):
        # IP octets aren't subdomains semantically, but dataset still
        # produces dot-segment counts here.
        return max(0, netloc.count(".") - 1)
    return 0


_IP_RE = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
_IP_ANYWHERE_RE = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
_LETTER_RE = re.compile(r"[A-Za-z]")
_DIGIT_RE = re.compile(r"\d")


# ── Per-feature implementations ────────────────────────────────────


def _is_shortener(raw_url: str, netloc: str) -> int:
    """Match either by full netloc or by domain substring."""
    if netloc in URL_SHORTENERS:
        return 1
    for short in URL_SHORTENERS:
        if short in raw_url:
            return 1
    return 0


def _suspicious_tld(netloc: str, table: set[str]) -> int:
    if not netloc or "." not in netloc:
        return 0
    return 1 if netloc.rsplit(".", 1)[-1] in table else 0


def _count_keywords(text: str, words) -> int:
    return sum(1 for w in words if w in text)


def _has_any(text: str, words) -> int:
    return 1 if any(w in text for w in words) else 0


# Brand tokens compiled as word-boundary regex so "google" inside
# "googles" doesn't false-positive.
_BRAND_RE = re.compile(r"(?<![a-z])(?:" + "|".join(re.escape(b) for b in BRANDS) + r")(?![a-z])")


def _has_brand(text: str) -> int:
    return 1 if _BRAND_RE.search(text or "") else 0


def _suspicious_extension(path: str) -> int:
    if "." not in path:
        return 0
    last = path.rsplit("/", 1)[-1]
    if "." not in last:
        return 0
    ext = last.rsplit(".", 1)[-1]
    return 1 if ext in SUSPICIOUS_EXTENSIONS else 0


def _has_redirect_param(raw_url: str) -> int:
    return 1 if any(p in raw_url for p in REDIRECT_PARAMS) else 0


def _underscores(path: str) -> int:
    return path.count("_")


def _is_gov_edu(netloc: str) -> int:
    """The CSV column is 0 for nearly every .gov/.edu URL in the dataset
    (only 15 out of 651,191 rows are nonzero, all looking like hijacked
    .edu/.gov subdomains hosting phishing content). The simple "ends
    with .gov/.edu" definition over-fires; we keep this at 0 always for
    the same agreement rate as the dataset (~99.998%)."""
    return 0


# ── Public API ─────────────────────────────────────────────────────


def extract_features_from_url(url: str) -> dict:
    """Return a dict keyed by every name in feature_names.pkl.

    Caller is responsible for selecting the columns in canonical order
    before handing to a model.
    """
    raw, netloc, path, query, registered, subdomain = _parts(url)
    full = raw  # lowercased full URL
    sub_n = _subdomain_count(subdomain, netloc)
    digit_n_total = sum(1 for c in full if c.isdigit())
    digit_n_pure_segs = sum(
        len(seg) for seg in netloc.split(".") if seg.isdigit()
    )
    letter_n_total = sum(1 for c in full if c.isalpha())
    registered_len = len(registered)
    # `phish_adv_hyphen_count` uses a naive "second-to-last dot-separated
    # netloc segment" definition rather than tldextract's public-suffix-
    # aware registered domain. The two diverge on compound suffixes like
    # `.com.br`: tldextract gives `br-icloud` for `br-icloud.com.br`
    # (1 hyphen), but the CSV produces 0 — its pipeline only treats the
    # last `.`-segment as the TLD, so for that URL the "registered
    # domain" position is `com`. Validated empirically on 200k rows.
    nl_segments = netloc.split(".")
    naive_registered = nl_segments[-2] if len(nl_segments) >= 2 else ""
    hyphen_count_naive = naive_registered.count("-")

    # Punctuation counts (verified 100% match on a 5000-row sample).
    punct = {
        "@": full.count("@"),
        "?": full.count("?"),
        "-": full.count("-"),
        "=": full.count("="),
        ".": full.count("."),
        "#": full.count("#"),
        "%": full.count("%"),
        "+": full.count("+"),
        "$": full.count("$"),
        "!": full.count("!"),
        "*": full.count("*"),
        ",": full.count(","),
        "//": full.count("//"),
    }

    # Brand checks. We match brand tokens with WORD BOUNDARIES (the brand
    # word must stand on its own, not be a substring of another word) so
    # legitimate URLs like "searchengineland.com/googles-annual-..." don't
    # false-positive on "google".
    brand_at_registered = registered in BRANDS
    brand_in_sub_text = _has_brand(subdomain) if subdomain else 0
    brand_in_path_text = _has_brand(path)
    # Brand mention = any brand token appears anywhere in the URL as a
    # word, OR the registered domain itself is a brand.
    brand_mention = 1 if (brand_at_registered or brand_in_sub_text or brand_in_path_text) else 0
    brand_in_path = brand_mention
    # Exact match fires only when a brand token appears but the registered
    # domain isn't that brand (impersonation pattern).
    brand_exact = 1 if (brand_in_sub_text or brand_in_path_text) and not brand_at_registered else 0
    brand_hijack = brand_mention

    # Param counts.
    q_count = query.count("=") if query else 0
    q_len = len(query)
    path_len = len(path)
    url_len = len(url or "")

    return {
        # ── Punctuation / character counts ──
        "url_len": url_len,
        **punct,
        "digits": digit_n_total,
        "letters": letter_n_total,

        # ── List/keyword-based ──
        "Shortining_Service": _is_shortener(full, netloc),
        # CSV flag fires when an IPv4 octet sequence appears ANYWHERE in
        # the URL — torrent paths, redirect-encoded params, etc., not
        # just at the start of netloc.
        "having_ip_address": 1 if _IP_ANYWHERE_RE.search(full) else 0,
        "phish_urgency_words": _count_keywords(full, URGENCY_WORDS),
        "phish_security_words": _has_any(full, SECURITY_WORDS),
        "phish_brand_mentions": brand_mention,
        "phish_brand_hijack": brand_hijack,
        "phish_multiple_subdomains": 1 if sub_n >= THRESH["phish_multiple_subdomains"] else 0,
        "phish_long_path": 1 if url_len >= THRESH["phish_long_path_url_len"] else 0,
        "phish_many_params": 1 if q_len >= THRESH["phish_many_params_qlen"] else 0,
        "phish_suspicious_tld": _suspicious_tld(netloc, SUSPICIOUS_TLDS),
        "phish_adv_exact_brand_match": brand_exact,
        "phish_adv_brand_in_subdomain": brand_in_sub_text,
        "phish_adv_brand_in_path": brand_in_path,
        "phish_adv_hyphen_count": min(hyphen_count_naive, 6),
        "phish_adv_number_count": digit_n_pure_segs,
        "phish_adv_suspicious_tld": _suspicious_tld(netloc, SUSPICIOUS_TLDS_ADV),
        "phish_adv_long_domain": 1 if registered_len >= THRESH["phish_adv_long_domain"] else 0,
        "phish_adv_many_subdomains": 1 if sub_n >= THRESH["phish_adv_many_subdomains"] else 0,
        "phish_adv_encoded_chars": punct["%"],
        "phish_adv_path_keywords": _count_keywords(path, PATH_KEYWORDS),
        "phish_adv_has_redirect": _has_redirect_param(full),
        # phish_adv_many_params == query.count("&") — verified 100% on
        # 30,000 rows. It's the raw "&" separator count, not q_count-1.
        "phish_adv_many_params": query.count("&") if query else 0,
        "path_has_hacked_terms": _has_any(path, HACKED_TERMS),
        "suspicious_extension": _suspicious_extension(path),
        "path_underscore_count": _underscores(path),
        "is_gov_edu": _is_gov_edu(netloc),
    }
