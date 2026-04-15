"""Password hashing and role-based access control helpers."""
import hashlib
import hmac
import os
import secrets
from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request

_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SALT_BYTES = 16


def hash_password(password: str) -> str:
    """Return a salted scrypt hash encoded as 'scrypt$<salt_hex>$<hash_hex>'."""
    salt = os.urandom(_SALT_BYTES)
    digest = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P
    )
    return f"scrypt${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, salt_hex, digest_hex = stored.split("$")
    except ValueError:
        return False
    if scheme != "scrypt":
        return False
    salt = bytes.fromhex(salt_hex)
    expected = bytes.fromhex(digest_hex)
    candidate = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P
    )
    return hmac.compare_digest(candidate, expected)


def role_required(*allowed_roles: str):
    """Decorator: require a valid JWT whose 'role' claim is in allowed_roles."""
    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            role = claims.get("role", "user")
            if role not in allowed_roles:
                return jsonify({"error": "forbidden", "required_roles": list(allowed_roles)}), 403
            return fn(*args, **kwargs)
        return decorated
    return wrapper


def generate_api_key() -> tuple[str, str]:
    """Return (plaintext_key, sha256_hash). Only the hash is stored."""
    key = "msk_" + secrets.token_urlsafe(32)
    return key, hashlib.sha256(key.encode()).hexdigest()


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()
