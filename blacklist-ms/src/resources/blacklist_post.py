from flask import Blueprint, request, jsonify
from datetime import datetime
import uuid
from ..models import db, Blacklist
from ..auth import require_bearer

bp = Blueprint("blacklist_post", __name__)

@bp.route("/blacklists", methods=["POST"])
@require_bearer
def add_blacklist():
    data = request.get_json(silent=True) or {}

    email = (data.get("email") or "").strip().lower()
    app_uuid_str = (data.get("app_uuid") or "").strip()
    reason = (data.get("blocked_reason") or "").strip() or None

    if not email or not app_uuid_str:
        return jsonify({"error": "email and app_uuid are required"}), 400

    # Validar que sea UUID y normalizar a string-canónico
    try:
        app_uuid_norm = str(uuid.UUID(app_uuid_str))
    except ValueError:
        return jsonify({"error": "app_uuid must be a valid UUID"}), 400

    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)

    bl = Blacklist.query.filter_by(email=email).first()
    if bl is None:
        bl = Blacklist(
            email=email,
            app_uuid=app_uuid_norm,
            blocked_reason=reason,
            request_ip=client_ip,
        )
        db.session.add(bl)
    else:
        bl.app_uuid = app_uuid_norm
        bl.blocked_reason = reason
        bl.request_ip = client_ip
        bl.created_at = datetime.utcnow()

    db.session.commit()
    return jsonify({"message": "blacklist updated", "email": email}), 201
