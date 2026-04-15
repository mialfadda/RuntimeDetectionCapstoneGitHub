"""Input validators: URL shape, email, XSS/SQLi heuristics (Step 34)."""
import re
from urllib.parse import urlparse

_URL_MAX_LEN = 2048
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_SQLI_PATTERNS = re.compile(
    r"(?i)(\bunion\b.+\bselect\b|\bdrop\b\s+\btable\b|;\s*--|/\*|\*/|\bxp_cmdshell\b)"
)
_XSS_PATTERNS = re.compile(r"(?i)(<script\b|javascript:|on\w+\s*=|<iframe\b)")


class ValidationError(ValueError):
    pass


def validate_url(url: str) -> str:
    if not isinstance(url, str) or not url:
        raise ValidationError("url is required")
    url = url.strip()
    if len(url) > _URL_MAX_LEN:
        raise ValidationError(f"url exceeds {_URL_MAX_LEN} chars")
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValidationError("url scheme must be http or https")
    if not parsed.netloc:
        raise ValidationError("url missing host")
    return url


def validate_email(email: str) -> str:
    if not isinstance(email, str) or not _EMAIL_RE.match(email):
        raise ValidationError("invalid email")
    return email.lower().strip()


def validate_password(pw: str) -> str:
    if not isinstance(pw, str) or len(pw) < 8:
        raise ValidationError("password must be >= 8 chars")
    if len(pw) > 256:
        raise ValidationError("password too long")
    return pw


def reject_injection(text: str, field: str = "input") -> str:
    """Reject obvious SQLi/XSS payloads. Belt-and-braces — ORM params are primary defense."""
    if not isinstance(text, str):
        return text
    if _SQLI_PATTERNS.search(text) or _XSS_PATTERNS.search(text):
        raise ValidationError(f"{field} contains disallowed characters")
    return text
