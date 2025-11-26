import os
import pytest
from application import application
from src.models import db

@pytest.fixture(scope="module")
def client():
    application.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )
    with application.app_context():
        db.create_all()
    with application.test_client() as c:
        yield c
    with application.app_context():
        db.drop_all()

def test_create_and_get(client):
    token = os.getenv("TOKEN", "change-me-very-strong")
    h = {"Authorization": f"Bearer {token}"}
    email = "ci-user@example.com"
    app_uuid = "11111111-1111-1111-1111-111111111111"

    r = client.post("/blacklists", json={
        "email": email,
        "app_uuid": app_uuid,
        "blocked_reason": "fraud"
    }, headers=h)
    assert r.status_code in (200, 201)

    r2 = client.get(f"/blacklists/{email}", headers=h)
    assert r2.status_code == 200
    body = r2.get_json()
    assert body.get("app_uuid") == app_uuid or body.get("email") == email