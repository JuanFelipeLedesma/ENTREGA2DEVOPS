# blacklist-ms/src/auth.py
import os
from functools import wraps
from flask import request, jsonify, current_app

# Valor por defecto útil para pruebas/CI
DEFAULT_TOKEN = os.getenv("TOKEN", "change-me-very-strong")


def _expect_token() -> str:
    """
    Resuelve el token esperado priorizando:
    1) env TOKEN
    2) current_app.config["TOKEN"] si existe
    3) DEFAULT_TOKEN
    """
    tok = os.getenv("TOKEN")
    if tok:
        return tok
    try:
        cfg = current_app.config  # válido en contexto de request
        if cfg.get("TOKEN"):
            return cfg["TOKEN"]
    except Exception:
        pass
    return DEFAULT_TOKEN


def _unauthorized(message: str):
    """401 con cabecera WWW-Authenticate para flujo Bearer."""
    resp = jsonify({"error": "unauthorized", "message": message})
    resp.status_code = 401
    resp.headers["WWW-Authenticate"] = 'Bearer realm="access", error="invalid_token"'
    return resp


def require_auth(fn):
    """
    Decorador:
    - 401 si falta el header Bearer.
    - 401 si el token es inválido.
    - pasa al handler si es válido.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return _unauthorized("Missing bearer token")

        provided = auth_header.split(" ", 1)[1].strip()
        expected = _expect_token()

        if provided != expected:
            return _unauthorized("Invalid token")

        return fn(*args, **kwargs)

    return wrapper


# ---- Alias de compatibilidad ----
# Algunos módulos importan `require_bearer` o `auth`.
require_bearer = require_auth
auth = require_auth

__all__ = ["require_auth", "require_bearer", "auth"]