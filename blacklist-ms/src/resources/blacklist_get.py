from flask import Blueprint, jsonify
from ..models import Blacklist
from ..auth import require_bearer

bp = Blueprint("blacklist_get", __name__)

@bp.route("/blacklists/<string:email>", methods=["GET"])
@require_bearer
def check_blacklist(email: str):
    email = (email or "").strip().lower()
    bl = Blacklist.query.filter_by(email=email).first()
    if bl:
        return jsonify({
            "blacklisted": True,
            "blocked_reason": bl.blocked_reason,
            "app_uuid": str(bl.app_uuid),
            "since": bl.created_at.isoformat() + "Z",
        }), 200
    return jsonify({"blacklisted": False, "blocked_reason": None}), 200
