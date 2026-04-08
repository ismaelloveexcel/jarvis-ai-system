def test_root_healthy(client):
    resp = client.get("/")
    assert resp.status_code in (200, 503)
    data = resp.json()
    assert "status" in data
    assert "app" in data
    assert "database" in data


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code in (200, 503)
    data = resp.json()
    assert "status" in data
    assert "database" in data


def test_root_returns_request_id(client):
    resp = client.get("/")
    assert "x-request-id" in resp.headers
