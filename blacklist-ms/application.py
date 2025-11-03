import os
import json
from flask import Flask, jsonify, request
from src.config import DATABASE_URL, PORT
from src.models import db
from src.resources.blacklist_post import bp as bp_post
from src.resources.blacklist_get import bp as bp_get

# ---- Feature flag (toggle por env var) ----
FEATURE_VERBOSE = os.getenv("FEATURE_VERBOSE", "false").lower() == "true"

# Elastic Beanstalk busca este objeto:
application = Flask(__name__)

# ---- Config DB ----
application.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
application.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
application.config["FEATURE_VERBOSE"] = FEATURE_VERBOSE  # disponible para quien lo necesite

# ---- Init DB y tablas ----
db.init_app(application)
with application.app_context():
    db.create_all()
try:
    # si tus modelos y el "db" están en src/models.py
    from src import models as _models
    _db = _models.db
except Exception:
    # fallback si usaste otro nombre/ubicación
    from src.database import db as _db  # o from src.db import db as _db

with application.app_context():
    _db.create_all()

# ---- Health ----
@application.route("/health", methods=["GET"])
def health():
    # Mantengo v6 como versión para esta estrategia de feature flags
    return jsonify({"status": "ok", "version": "v6", "feature_verbose": FEATURE_VERBOSE}), 200

# ---- Blueprints existentes ----
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
            # Intenta parsear JSON de la respuesta
            payload = None
            try:
                # Flask 2.x: get_json(silent=True) existe en Request, no en Response.
                # Para Response usamos response.get_data y json.loads
                payload = json.loads(response.get_data(as_text=True))
            except Exception:
                payload = None

            # Esperamos un dict con 'email'
            if isinstance(payload, dict) and "email" in payload:
                # Si ya viene blocked_reason no tocamos nada
                if "blocked_reason" not in payload:
                    # Import aquí para evitar dependencias circulares al importar modelos
                    from src.models import Blacklist  # ajusta al nombre real del modelo si difiere

                    email_value = payload["email"]
                    with application.app_context():
                        row = (
                            Blacklist.query.filter_by(email=email_value)
                            .order_by(Blacklist.created_at.desc() if hasattr(Blacklist, "created_at") else None)
                            .first()
                        )
                        if row and getattr(row, "blocked_reason", None):
                            payload["blocked_reason"] = row.blocked_reason

                    # Reescribe el cuerpo de la respuesta
                    response.set_data(json.dumps(payload))
                    # Asegura header correcto
                    response.headers["Content-Type"] = "application/json; charset=utf-8"
    except Exception:
        # No rompas la respuesta por un fallo del enriquecimiento
        pass

    return response

# ---- Run local ----
if __name__ == "__main__":
    application.run(host="0.0.0.0", port=PORT)