# blacklist-ms/src/resources/blacklist_get.py
from flask import Blueprint, jsonify
from ..auth import require_bearer
from ..models import Blacklist

bp = Blueprint("blacklist_get", __name__)

@bp.route("/blacklists/<string:email>", methods=["GET"])
@require_bearer
def get_blacklist(email: str):
    """
    Responde:
      - 200 si existe: {'email','app_uuid','blacklisted':True,['blocked_reason']}
      - 404 si no existe: {'error':'not found','email','blacklisted':False}
    """
    q = Blacklist.query.filter_by(email=email)
    try:
        row = q.order_by(Blacklist.created_at.desc()).first()
    except Exception:
        row = q.first()

    if row is None:
        return jsonify({
            "error": "not found",
            "email": email,
            "blacklisted": False
        }), 404

    payload = {
        "email": row.email,
        # Si app_uuid es UUID o string, str(...) lo deja listo para JSON
        "app_uuid": str(getattr(row, "app_uuid", "")) or None,
        "blacklisted": True,
    }
    if getattr(row, "blocked_reason", None):
        payload["blocked_reason"] = row.blocked_reason

    return jsonify(payload), 200