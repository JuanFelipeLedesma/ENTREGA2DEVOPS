# blacklist-ms/src/resources/blacklist_get.py
from flask import Blueprint, jsonify
from ..auth import require_bearer  # alias disponible en src/auth.py
from ..models import Blacklist

bp = Blueprint("blacklist_get", __name__)

@bp.get("/blacklists/<string:email>")
@require_bearer
def get_blacklist(email: str):
    # Busca el registro más reciente por si hay múltiples entradas históricas
    row = (
        Blacklist.query.filter_by(email=email)
        .order_by(Blacklist.created_at.desc() if hasattr(Blacklist, "created_at") else None)
        .first()
    )

    # Si no existe, responde 404 (esto es lo que el test espera)
    if row is None:
        return jsonify({
            "error": "not found",
            "email": email,
            "blacklisted": False
        }), 404

    # Si existe, responde 200 con el contrato mínimo
    payload = {
        "email": row.email,
        "blacklisted": True,
    }
    # Incluye blocked_reason si existe (tu after_request puede enriquecer también)
    if getattr(row, "blocked_reason", None):
        payload["blocked_reason"] = row.blocked_reason

    return jsonify(payload), 200