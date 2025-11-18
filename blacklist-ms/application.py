# src/application.py
import os
import json
from flask import Flask, jsonify, request
from sqlalchemy import inspect
from sqlalchemy.pool import StaticPool

from src.config import DATABASE_URL as CFG_DATABASE_URL, PORT
from src.models import db, Blacklist  # importa el modelo para registrar metadata

# ---- Feature flag ----
FEATURE_VERBOSE = os.getenv("FEATURE_VERBOSE", "false").lower() == "true"

# ---- App ----
application = Flask(__name__)

# ---- DB URL (permitimos override del test) ----
DB_URL = os.getenv("DATABASE_URL", CFG_DATABASE_URL)
application.config["SQLALCHEMY_DATABASE_URI"] = DB_URL
application.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
application.config["FEATURE_VERBOSE"] = FEATURE_VERBOSE

# ---- Engine options para SQLite (crítico para :memory:) ----
engine_opts = dict(application.config.get("SQLALCHEMY_ENGINE_OPTIONS", {}))
if DB_URL.startswith("sqlite:///:memory:"):
    # Un solo connection para todo el proceso → el esquema no se “pierde”
    engine_opts.update({
        "poolclass": StaticPool,
        "connect_args": {"check_same_thread": False},
    })
elif DB_URL.startswith("sqlite:///"):
    engine_opts.update({
        "connect_args": {"check_same_thread": False},
    })
if engine_opts:
    application.config["SQLALCHEMY_ENGINE_OPTIONS"] = engine_opts

# ---- Inicializa SQLAlchemy ----
db.init_app(application)

def _ensure_schema():
    """Crea tablas si aún no existen en el engine ACTIVO."""
    try:
        insp = inspect(db.engine)
        if "blacklists" not in insp.get_table_names():
            db.create_all()
    except Exception:
        # no bloquear el request por esta verificación
        pass

# 1) Defensa en import/arranque
with application.app_context():
    _ensure_schema()

# 2) Defensa en cada request (evita el fallo del test de endpoints)
@application.before_request
def _ensure_schema_before_request():
    _ensure_schema()

# ---- Health ----
@application.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "version": "v7",
        "feature_verbose": FEATURE_VERBOSE,
    }), 200

# ---- Blueprints ----
from src.resources.blacklist_post import bp as bp_post
from src.resources.blacklist_get import bp as bp_get
application.register_blueprint(bp_post)
application.register_blueprint(bp_get)

# ---- Enriquecimiento condicional de respuesta (GET /blacklists/<email>) ----
@application.after_request
def maybe_augment_blacklist_get(response):
    try:
        if (
            FEATURE_VERBOSE
            and request.method == "GET"
            and request.path.startswith("/blacklists/")
            and response.content_type
            and response.content_type.startswith("application/json")
        ):
            try:
                payload = json.loads(response.get_data(as_text=True))
            except Exception:
                payload = None

            if isinstance(payload, dict) and "email" in payload and "blocked_reason" not in payload:
                row = (
                    Blacklist.query.filter_by(email=payload["email"])
                    .order_by(getattr(Blacklist, "created_at", None).desc() if hasattr(Blacklist, "created_at") else None)
                    .first()
                )
                if row and getattr(row, "blocked_reason", None):
                    payload["blocked_reason"] = row.blocked_reason
                    response.set_data(json.dumps(payload))
                    response.headers["Content-Type"] = "application/json; charset=utf-8"
    except Exception:
        pass
    return response

# ---- Run local ----
if __name__ == "__main__":
    application.run(host="0.0.0.0", port=PORT)