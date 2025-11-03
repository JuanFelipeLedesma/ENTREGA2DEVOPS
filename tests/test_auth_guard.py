import os
import pytest

# Asegura el mismo entorno que el resto de tests
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["TOKEN"] = "change-me-very-strong"

from application import application  # noqa: E402


@pytest.fixture
def client():
    with application.test_client() as c:
        yield c


def test_auth_missing_token(client):
    # Debe rechazar si no mandamos Authorization
    r = client.get("/blacklists/alguien@example.com")
    assert r.status_code == 401


def test_auth_bad_token(client):
    # Debe rechazar si el token es incorrecto
    r = client.get(
        "/blacklists/alguien@example.com",
        headers={"Authorization": "Bearer not-the-right-one"},
    )
    assert r.status_code == 401