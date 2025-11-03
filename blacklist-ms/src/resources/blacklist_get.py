# blacklist-ms/src/resources/blacklist_get.py
from flask import Blueprint, jsonify
from ..auth import require_bearer
from ..models import Blacklist

bp = Blueprint("blacklist_get", __name__)

@bp.route("/blacklists/<string:email>", methods=["GET"])
@require_bearer
def get_blacklist(email: str):
    """
    Devuelve el estado de blacklist para un email.
    - 200 si existe, con payload {'email', 'blacklisted': True, ['blocked_reason']}.
    - 404 si no existe, con payload {'error': 'not found', 'email', 'blacklisted': False}.
    """
    q = Blacklist.query.filter_by(email=email)
    # Si el modelo tiene created_at, usa el más reciente; si no, .first() igualmente funciona.
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
        "blacklisted": True,
    }
    if getattr(row, "blocked_reason", None):
        payload["blocked_reason"] = row.blocked_reason

    return jsonify(payload), 200