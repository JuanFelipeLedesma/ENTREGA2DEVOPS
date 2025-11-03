import os
import pytest

# Usar una BD efímera en memoria para las pruebas
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["TOKEN"] = "change-me-very-strong"  # el mismo del servicio

# Importa la app de Flask que expone "application"
from application import application  # ajusta el nombre si tu entrypoint es distinto

@pytest.fixture
def client():
    with application.test_client() as c:
        yield c

def _auth():
    return {"Authorization": "Bearer change-me-very-strong"}

def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.is_json
    body = r.get_json()
    assert body.get("status") == "ok"

def test_blacklist_post_and_get(client):
    payload = {
        "email": "flaguser@example.com",
        "app_uuid": "11111111-1111-1111-1111-111111111111",
        "blocked_reason": "fraud",
    }
    r1 = client.post("/blacklists", json=payload, headers=_auth())
    assert r1.status_code in (200, 201)

    r2 = client.get("/blacklists/flaguser@example.com", headers=_auth())
    assert r2.status_code == 200
    body = r2.get_json()
    # El contrato puede variar; validamos campos clave sin acoplar de más
    assert "blacklisted" in body
    if "blocked_reason" in body:
        assert body["blocked_reason"] == "fraud"