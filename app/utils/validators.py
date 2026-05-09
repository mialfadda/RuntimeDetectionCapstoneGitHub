import re

class ValidationError(Exception):
    pass

def validate_email(e):
    e = e.strip().lower()
    if not e or '@' not in e:
        raise ValidationError('Invalid email')
    return e

def validate_password(p):
    if len(p) < 8:
        raise ValidationError('Password must be 8+ characters')
    return p

def validate_url(url: str) -> str:
    url = url.strip()
    if not url:
        raise ValidationError('URL is required')
    if len(url) > 3000:
        raise ValidationError('URL too long')
    if not (url.startswith('http://') or url.startswith('https://')):
        raise ValidationError('URL must start with http:// or https://')
    return url

def reject_injection(value: str, field: str) -> str:
    """Basic SQL/XSS injection rejection."""
    if not isinstance(value, str):
        return value
    dangerous = ["'", '"', ';', '--', '<script', 'DROP TABLE', 'SELECT *']
    for d in dangerous:
        if d.lower() in value.lower():
            raise ValidationError(f'Invalid characters in {field}')
    return value
