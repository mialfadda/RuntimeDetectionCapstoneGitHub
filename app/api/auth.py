from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt, get_jwt_identity, jwt_required
from app.database.models import User, db
from app.utils.auth import hash_password, verify_password
from app.utils.validators import ValidationError, validate_email, validate_password
auth_bp = Blueprint("auth", __name__)
_REVOKED = set()
def _tokens(u):
    c={"role":u.role,"email":u.email}
    return {"access_token":create_access_token(identity=str(u.userID),additional_claims=c),"refresh_token":create_refresh_token(identity=str(u.userID),additional_claims=c),"role":u.role}
@auth_bp.post("/register")
def register():
    d=request.get_json(silent=True) or {}
    try: email=validate_email(d.get("email","")); pw=validate_password(d.get("password",""))
    except ValidationError as e: return jsonify({"error":str(e)}),400
    if User.query.filter_by(email=email).first(): return jsonify({"error":"email already registered"}),409
    u=User(name=(d.get("name") or email.split("@")[0])[:100],email=email,role="user",passwordHash=hash_password(pw))
    db.session.add(u); db.session.commit()
    return jsonify({"user_id":u.userID,**_tokens(u)}),201
@auth_bp.post("/login")
def login():
    d=request.get_json(silent=True) or {}
    u=User.query.filter_by(email=(d.get("email") or "").strip().lower()).first()
    if not u or not verify_password(d.get("password",""),u.passwordHash): return jsonify({"error":"invalid credentials"}),401
    return jsonify({"user_id":u.userID,**_tokens(u)}),200
@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    uid=get_jwt_identity(); claims=get_jwt()
    u=db.session.get(User,int(uid))
    if not u: return jsonify({"error":"user not found"}),404
    return jsonify({"access_token":create_access_token(identity=uid,additional_claims={"role":u.role,"email":u.email})}),200
@auth_bp.post("/logout")
@jwt_required()
def logout(): _REVOKED.add(get_jwt()["jti"]); return jsonify({"message":"logged out"}),200
@auth_bp.get("/me")
@jwt_required()
def me():
    u=db.session.get(User,int(get_jwt_identity()))
    return jsonify({"user_id":u.userID,"email":u.email,"role":u.role,"name":u.name}) if u else (jsonify({"error":"not found"}),404)
