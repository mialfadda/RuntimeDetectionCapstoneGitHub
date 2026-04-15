"""Authentication: login, refresh, logout, register + JWT middleware (Step 11)."""
from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)

from app.database.models import User, db
from app.utils.auth import hash_password, verify_password
from app.utils.validators import ValidationError, validate_email, validate_password

auth_bp = Blueprint("auth", __name__)

# In-memory revocation set. Replace with Redis-backed store in Phase 11.
_REVOKED_JTIS: set[str] = set()


def _issue_tokens(user: User) -> dict:
    claims = {"role": user.role, "email": user.email}
    access = create_access_token(identity=str(user.userID), additional_claims=claims)
    refresh = create_refresh_token(identity=str(user.userID), additional_claims=claims)
    return {"access_token": access, "refresh_token": refresh, "role": user.role}


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    try:
        email = validate_email(data.get("email", ""))
        password = validate_password(data.get("password", ""))
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    name = (data.get("name") or email.split("@")[0])[:100]
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "email already registered"}), 409
    user = User(name=name, email=email, role="user", passwordHash=hash_password(password))
    db.session.add(user)
    db.session.commit()
    return jsonify({"user_id": user.userID, **_issue_tokens(user)}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    user = User.query.filter_by(email=email).first()
    if not user or not verify_password(password, user.passwordHash):
        return jsonify({"error": "invalid credentials"}), 401
    return jsonify({"user_id": user.userID, **_issue_tokens(user)}), 200


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    user = db.session.get(User, int(identity))
    if not user:
        return jsonify({"error": "user not found"}), 404
    access = create_access_token(
        identity=identity, additional_claims={"role": user.role, "email": user.email}
    )
    return jsonify({"access_token": access}), 200


@auth_bp.post("/logout")
@jwt_required()
def logout():
    _REVOKED_JTIS.add(get_jwt()["jti"])
    return jsonify({"message": "logged out"}), 200


@auth_bp.get("/me")
@jwt_required()
def me():
    user = db.session.get(User, int(get_jwt_identity()))
    if not user:
        return jsonify({"error": "user not found"}), 404
    return jsonify({"user_id": user.userID, "email": user.email, "role": user.role, "name": user.name})


def is_jti_revoked(jti: str) -> bool:
    return jti in _REVOKED_JTIS
