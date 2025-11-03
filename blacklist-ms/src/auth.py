from flask import request, jsonify
from functools import wraps
from .config import AUTH_TOKEN

def require_bearer(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Missing Bearer Token"}), 401
        token = auth.split(" ", 1)[1]
        if token != AUTH_TOKEN:
            return jsonify({"error": "Invalid token"}), 403
        return fn(*args, **kwargs)
    return wrapper
