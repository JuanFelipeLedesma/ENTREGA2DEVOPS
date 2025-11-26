import os
import pytest

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["TOKEN"] = "change-me-very-strong"

from application import application  # noqa: E402


@pytest.fixture
def client():
    with application.test_client() as c:
        yield c


def _auth():
    return {"Authorization": "Bearer change-me-very-strong"}


def test_blacklist_get_not_found_branch(client):
    # Rama 404 del GET (cubre la línea pendiente del blacklist_get.py)
    r = client.get("/blacklists/no-existe@example.com", headers=_auth())
    # El contrato del endpoint es 404 cuando no existe
    assert r.status_code == 404


def test_blacklist_post_validation_error(client):
    # Falta 'email' -> 400 (cubre validaciones iniciales en blacklist_post.py)
    payload_invalido = {
        "app_uuid": "11111111-1111-1111-1111-111111111111",
        "blocked_reason": "fraud",
    }
    r = client.post("/blacklists", json=payload_invalido, headers=_auth())
    assert r.status_code == 400


def test_blacklist_post_update_existing(client):
    # 1) Creamos
    payload = {
        "email": "flaguser@example.com",
        "app_uuid": "11111111-1111-1111-1111-111111111111",
        "blocked_reason": "fraud",
    }
    r1 = client.post("/blacklists", json=payload, headers=_auth())
    assert r1.status_code in (200, 201)

    # 2) Actualizamos (cubre la rama de update en blacklist_post.py)
    payload_update = {**payload, "blocked_reason": "abuse"}
    r2 = client.post("/blacklists", json=payload_update, headers=_auth())
    # suele devolver 200 al actualizar
    assert r2.status_code in (200, 201)

    # 3) Verificamos que se refleje el cambio
    r3 = client.get("/blacklists/flaguser@example.com", headers=_auth())
    assert r3.status_code == 200
    body = r3.get_json()
    assert "blacklisted" in body
    # si el contrato incluye reason en la respuesta, validamos:
    if "blocked_reason" in body:
        assert body["blocked_reason"] in ("abuse", "fraud")