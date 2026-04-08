def test_action_allowed(client, seed_user):
    resp = client.post("/actions/", json={
        "user_id": 1,
        "action_name": "create_file",
        "payload": {"relative_path": "example/test.txt", "content": "hello"},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"]["status"] in ("success", "completed")


def test_action_blocked(client, seed_user):
    resp = client.post("/actions/", json={
        "user_id": 1,
        "action_name": "http_request",
        "payload": {"url": "https://evil.com"},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"]["status"] == "blocked"


def test_action_approval_required(client, seed_user):
    resp = client.post("/actions/", json={
        "user_id": 1,
        "action_name": "create_file",
        "payload": {"relative_path": "restricted/secret.txt", "content": "needs approval"},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"]["status"] == "pending_approval"


def test_action_delete_blocked(client, seed_user):
    resp = client.post("/actions/", json={
        "user_id": 1,
        "action_name": "delete_file",
        "payload": {"path": "/etc/passwd"},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"]["status"] == "blocked"
