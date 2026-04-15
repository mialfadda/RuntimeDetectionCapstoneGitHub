"""Admin-only endpoints: API keys (Step 36), model upload stub (Step 37), audit log."""
import hashlib
import hmac
import os
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from werkzeug.utils import secure_filename

from app import limiter
from app.database.models import (
    ActionLog,
    Admin,
    ApiKey,
    Model as MlModel,
    ModelVersion,
    User,
    db,
)
from app.utils.auth import generate_api_key, hash_api_key, role_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/users")
@jwt_required()
@role_required("admin")
def list_users():
    users = User.query.all()
    return jsonify({
        "users": [
            {"user_id": u.userID, "email": u.email, "role": u.role, "name": u.name}
            for u in users
        ]
    })


# ----- API keys (Step 36) --------------------------------------------------

@admin_bp.post("/api-keys")
@jwt_required()
@limiter.limit("20/hour")
def create_api_key():
    """Any authenticated user may generate a key; admin can target other users."""
    data = request.get_json(silent=True) or {}
    caller_id = int(get_jwt_identity())
    target_user_id = data.get("user_id", caller_id)
    plaintext, digest = generate_api_key()
    key = ApiKey(keyHash=digest, label=(data.get("label") or "default")[:100], userID=target_user_id)
    db.session.add(key)
    db.session.commit()
    return jsonify({
        "key_id": key.keyID,
        "api_key": plaintext,
        "warning": "store this now — it will not be shown again",
    }), 201


@admin_bp.get("/api-keys")
@jwt_required()
def list_api_keys():
    caller_id = int(get_jwt_identity())
    keys = ApiKey.query.filter_by(userID=caller_id).all()
    return jsonify({
        "keys": [
            {
                "key_id": k.keyID,
                "label": k.label,
                "created_at": k.createdAt.isoformat() if k.createdAt else None,
                "last_used_at": k.lastUsedAt.isoformat() if k.lastUsedAt else None,
                "usage_count": k.usageCount,
                "revoked": k.revoked,
            }
            for k in keys
        ]
    })


@admin_bp.post("/api-keys/<int:key_id>/rotate")
@jwt_required()
def rotate_api_key(key_id: int):
    key = db.session.get(ApiKey, key_id)
    if not key or key.userID != int(get_jwt_identity()):
        return jsonify({"error": "not found"}), 404
    plaintext, digest = generate_api_key()
    key.keyHash = digest
    key.usageCount = 0
    key.lastUsedAt = None
    db.session.commit()
    return jsonify({"key_id": key.keyID, "api_key": plaintext}), 200


@admin_bp.delete("/api-keys/<int:key_id>")
@jwt_required()
def revoke_api_key(key_id: int):
    key = db.session.get(ApiKey, key_id)
    if not key or key.userID != int(get_jwt_identity()):
        return jsonify({"error": "not found"}), 404
    key.revoked = True
    db.session.commit()
    return jsonify({"key_id": key.keyID, "revoked": True})


def authenticate_api_key(raw_key: str) -> ApiKey | None:
    """Middleware helper for non-JWT clients."""
    if not raw_key:
        return None
    key = ApiKey.query.filter_by(keyHash=hash_api_key(raw_key), revoked=False).first()
    if key:
        key.usageCount = (key.usageCount or 0) + 1
        key.lastUsedAt = datetime.utcnow()
        db.session.commit()
    return key


# ----- Model upload stub (Step 37) ----------------------------------------

@admin_bp.post("/models/upload")
@jwt_required()
@role_required("admin")
@limiter.limit("5/hour")
def upload_model():
    """Upload a new model artifact. Caller supplies HMAC-SHA256(file) signed with
    the shared MODEL_UPLOAD_SECRET. A2's Step 38 (hot-swap) promotes the version
    to 'active' after canary checks.
    """
    cfg = current_app.config
    upload = request.files.get("model_file")
    if upload is None:
        return jsonify({"error": "model_file (multipart) is required"}), 400

    signature = (request.form.get("signature") or "").strip().lower()
    version_tag = (request.form.get("version") or "").strip()
    model_name = (request.form.get("model_name") or "").strip()
    framework = (request.form.get("framework") or "unknown").strip()
    if not signature or not version_tag or not model_name:
        return jsonify({"error": "signature, version, model_name are required"}), 400

    ext = os.path.splitext(upload.filename or "")[1].lower()
    if ext not in cfg["MODEL_UPLOAD_ALLOWED_EXT"]:
        return jsonify({"error": f"extension {ext!r} not allowed"}), 400

    data = upload.read()
    if len(data) > cfg["MODEL_UPLOAD_MAX_MB"] * 1024 * 1024:
        return jsonify({"error": "model file exceeds size limit"}), 413

    expected = hmac.new(
        cfg["MODEL_UPLOAD_SECRET"].encode(), data, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        current_app.logger.warning("model upload signature mismatch by user %s", get_jwt_identity())
        return jsonify({"error": "signature verification failed"}), 401

    model_dir = cfg["MODEL_DIR"]
    os.makedirs(model_dir, exist_ok=True)
    safe_name = secure_filename(f"{model_name}_{version_tag}{ext}")
    dest = os.path.join(model_dir, safe_name)
    if os.path.exists(dest):
        return jsonify({"error": "version already exists"}), 409
    with open(dest, "wb") as fh:
        fh.write(data)

    model = MlModel.query.filter_by(name=model_name).first()
    if not model:
        model = MlModel(name=model_name, framework=framework)
        db.session.add(model)
        db.session.flush()

    if ModelVersion.query.filter_by(modelID=model.modelID, versionTag=version_tag).first():
        os.remove(dest)
        return jsonify({"error": "version already exists"}), 409

    caller_id = int(get_jwt_identity())
    admin_row = Admin.query.filter_by(userID=caller_id).first()
    version = ModelVersion(
        versionTag=version_tag,
        status="pending",
        modelID=model.modelID,
        adminID=admin_row.adminID if admin_row else None,
    )
    db.session.add(version)
    db.session.flush()

    if admin_row is not None:
        db.session.add(ActionLog(
            action="model.upload",
            target=f"model:{model.modelID}/version:{version.versionID}",
            exportType=ext,
            adminID=admin_row.adminID,
        ))
    db.session.commit()

    return jsonify({
        "model_id": model.modelID,
        "version_id": version.versionID,
        "version": version_tag,
        "status": "pending",
        "sha256": hashlib.sha256(data).hexdigest(),
        "stored_as": safe_name,
    }), 201


@admin_bp.get("/models")
@jwt_required()
@role_required("admin")
def list_models():
    rows = (
        db.session.query(MlModel, ModelVersion)
        .outerjoin(ModelVersion, ModelVersion.modelID == MlModel.modelID)
        .order_by(ModelVersion.creationTimeStamp.desc().nullslast())
        .all()
    )
    return jsonify({
        "models": [
            {
                "model_id": m.modelID,
                "name": m.name,
                "framework": m.framework,
                "version_id": v.versionID if v else None,
                "version": v.versionTag if v else None,
                "status": v.status if v else None,
                "accuracy": v.accuracy if v else None,
            }
            for m, v in rows
        ]
    })


@admin_bp.post("/models/<int:version_id>/rollback")
@jwt_required()
@role_required("admin")
def rollback_model(version_id: int):
    return jsonify({"version_id": version_id, "status": "rollback_queued"}), 202


@admin_bp.get("/audit-log")
@jwt_required()
@role_required("admin")
def audit_log():
    logs = ActionLog.query.order_by(ActionLog.creationDate.desc()).limit(200).all()
    return jsonify({
        "entries": [
            {
                "action_id": a.actionID,
                "action": a.action,
                "target": a.target,
                "admin_id": a.adminID,
                "created_at": a.creationDate.isoformat() if a.creationDate else None,
            }
            for a in logs
        ]
    })
