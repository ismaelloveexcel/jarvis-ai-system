"""Tests for async execution (BackgroundTasks, 202 response)."""


def test_execution_returns_202(client, seed_user):
    resp = client.post("/execution/openhands", json={
        "request_type": "code_generation",
        "title": "Test gen",
        "objective": "Generate hello world",
    })
    assert resp.status_code == 202
    data = resp.json()
    assert data["execution_mode"] == "async"
    assert data["result"]["status"] == "accepted"
    assert "task_id" in data


def test_execution_status_endpoint(client, seed_user):
    resp = client.post("/execution/openhands", json={
        "request_type": "code_generation",
        "title": "Status check",
        "objective": "Test objective",
    })
    task_id = resp.json()["task_id"]

    status_resp = client.get(f"/execution/status/{task_id}")
    assert status_resp.status_code == 200
    assert status_resp.json()["task_id"] == task_id


def test_github_execution_returns_202(client, seed_user):
    resp = client.post("/execution/github/", json={
        "request_type": "repo_inspect",
        "title": "Inspect repo",
        "objective": "Check structure",
    })
    assert resp.status_code == 202
    assert resp.json()["execution_mode"] == "async"


def test_ops_request_returns_202(client, seed_user):
    resp = client.post("/ops/request", json={
        "request_type": "maintenance_check",
        "title": "Check health",
    })
    assert resp.status_code == 202
    assert resp.json()["execution_mode"] == "async"


def test_execution_status_not_found(client, seed_user):
    resp = client.get("/execution/status/99999")
    assert resp.status_code == 404
