# tests/test_api.py
import os, json, pytest

# Forzamos DB local/efímera para CI
os.environ["DATABASE_URL"] = "sqlite:///ci.sqlite3"
os.environ["PORT"] = "5000"
os.environ["FEATURE_VERBOSE"] = "false"  # puedes activarlo si quieres probar ese flag

from application import application, db

TOKEN = "change-me-very-strong"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

@pytest.fixture(autouse=True)
def _db_setup(tmp_path):
    # DB limpia por test
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path/'test.sqlite3'}"
    with application.app_context():
        db.drop_all()
        db.create_all()
    yield

def test_health_ok():
    with application.test_client() as c:
        r = c.get("/health")
        assert r.status_code == 200
        b = r.get_json()
        assert b["status"] == "ok"

def test_post_blacklist_crea_o_actualiza():
    with application.test_client() as c:
        payload = {
            "email": "ci_user@example.com",
            "app_uuid": "11111111-1111-1111-1111-111111111111",
            "blocked_reason": "fraud"
        }
        r = c.post("/blacklists", headers=HEADERS, data=json.dumps(payload))
        assert r.status_code in (200, 201)

def test_get_blacklist_por_email():
    with application.test_client() as c:
        payload = {
            "email": "ci_get@example.com",
            "app_uuid": "11111111-1111-1111-1111-111111111111",
            "blocked_reason": "fraud"
        }
        c.post("/blacklists", headers=HEADERS, data=json.dumps(payload))
        r = c.get("/blacklists/ci_get@example.com", headers={"Authorization": f"Bearer {TOKEN}"})
        assert r.status_code == 200
        b = r.get_json()
        # al menos verifica campos clave
        assert b.get("app_uuid") == "11111111-1111-1111-1111-111111111111"