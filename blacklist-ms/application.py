# src/application.py
import os
import json
from flask import Flask, jsonify, request
from sqlalchemy.pool import StaticPool

# Config propia
from src.config import DATABASE_URL as CFG_DATABASE_URL, PORT
# Importa el db y los modelos para registrar el metadata antes de create_all()
from src.models import db, Blacklist  # si hay más modelos, impórtalos aquí

# ---- Feature flag (toggle por env var) ----
FEATURE_VERBOSE = os.getenv("FEATURE_VERBOSE", "false").lower() == "true"

# Elastic Beanstalk y los tests esperan este objeto:
application = Flask(__name__)

# ---- Config DB (permite que el test sobreescriba por env) ----
DB_URL = os.getenv("DATABASE_URL", CFG_DATABASE_URL)
application.config["SQLALCHEMY_DATABASE_URI"] = DB_URL
application.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
application.config["FEATURE_VERBOSE"] = FEATURE_VERBOSE

# Caso especial: SQLite en memoria → una sola conexión viva para que no se
# “pierdan” las tablas entre create_all() y las sesiones del ORM.
engine_opts = dict(application.config.get("SQLALCHEMY_ENGINE_OPTIONS", {}))
if DB_URL.startswith("sqlite:///:memory:"):
    engine_opts.update({
        "poolclass": StaticPool,
        "connect_args": {"check_same_thread": False},
    })
elif DB_URL.startswith("sqlite:///"):
    # Para archivos SQLite locales es útil desactivar check_same_thread
    engine_opts.update({
        "connect_args": {"check_same_thread": False},
    })
if engine_opts:
    application.config["SQLALCHEMY_ENGINE_OPTIONS"] = engine_opts

# ---- Inicializa SQLAlchemy y crea tablas ----
# (db se define en src/models.py como db = SQLAlchemy())
db.init_app(application)
with application.app_context():
    db.create_all()  # crea todas las tablas una vez cargados los modelos

# ---- Health ----
@application.route("/health", methods=["GET"])
def health():
    # Mantengo v6 como versión para tu estrategia de flags
    return jsonify({
        "status": "ok",
        "version": "v6",
        "feature_verbose": FEATURE_VERBOSE
    }), 200

# ---- Blueprints existentes ----
from src.resources.blacklist_post import bp as bp_post
from src.resources.blacklist_get import bp as bp_get
application.register_blueprint(bp_post)
application.register_blueprint(bp_get)

# ---- Enriquecimiento condicional de respuesta (solo GET /blacklists/<email>) ----
@application.after_request
def maybe_augment_blacklist_get(response):
    """
    Si FEATURE_VERBOSE=true y la ruta es GET /blacklists/<email>,
    añade 'blocked_reason' al JSON de respuesta si está en la base de datos
    y aún no vino en la respuesta.
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
                # Usamos la sesión actual del ORM (no abrimos otro app_context)
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
        # No rompas la respuesta por un fallo del enriquecimiento
        pass

    return response

# ---- Run local ----
if __name__ == "__main__":
    application.run(host="0.0.0.0", port=PORT)