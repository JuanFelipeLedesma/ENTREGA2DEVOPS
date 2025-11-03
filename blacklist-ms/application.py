# src/application.py
import os
import json
from flask import Flask, jsonify, request
from sqlalchemy.pool import StaticPool
from sqlalchemy import inspect

from src.config import DATABASE_URL as CFG_DATABASE_URL, PORT
from src.models import db, Blacklist  # importa modelos ANTES de create_all para registrar metadata

# ---- Feature flag (toggle por env var) ----
FEATURE_VERBOSE = os.getenv("FEATURE_VERBOSE", "false").lower() == "true"

# Elastic Beanstalk / tests esperan este objeto:
application = Flask(__name__)

# ---- Config DB (permitimos override por env en tests) ----
DB_URL = os.getenv("DATABASE_URL", CFG_DATABASE_URL)
application.config["SQLALCHEMY_DATABASE_URI"] = DB_URL
application.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
application.config["FEATURE_VERBOSE"] = FEATURE_VERBOSE

# Engine options especiales para SQLite
engine_opts = dict(application.config.get("SQLALCHEMY_ENGINE_OPTIONS", {}))
if DB_URL.startswith("sqlite:///:memory:"):
    # Misma conexión para toda la vida del proceso → el esquema no “desaparece”
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

# ---- Inicializa SQLAlchemy y crea tablas (primera defensa) ----
db.init_app(application)
with application.app_context():
    db.create_all()

# ---- Segunda defensa: garantizar esquema antes del 1er request ----
@application.before_first_request
def _ensure_schema_on_first_request():
    try:
        insp = inspect(db.engine)
        # Si por cualquier motivo el engine actual no tiene las tablas, créalas
        if "blacklists" not in insp.get_table_names():
            db.create_all()
    except Exception:
        # No bloquear el arranque por esta verificación; los tests lo reflejarán
        pass

# ---- Health ----
@application.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "version": "v6",
        "feature_verbose": FEATURE_VERBOSE
    }), 200

# ---- Blueprints ----
from src.resources.blacklist_post import bp as bp_post
from src.resources.blacklist_get import bp as bp_get
application.register_blueprint(bp_post)
application.register_blueprint(bp_get)

# ---- Enriquecimiento condicional de respuesta (solo GET /blacklists/<email>) ----
@application.after_request
def maybe_augment_blacklist_get(response):
    """
    Si FEATURE_VERBOSE=true y la ruta es GET /blacklists/<email>,
    añade 'blocked_reason' si existe en BD y aún no vino en la respuesta.
    """
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