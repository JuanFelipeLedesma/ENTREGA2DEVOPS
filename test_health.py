from application import application
def test_health():
    c = application.test_client()
    r = c.get("/health")
    assert r.status_code == 200
    assert r.is_json
    assert r.get_json().get("status") == "ok"