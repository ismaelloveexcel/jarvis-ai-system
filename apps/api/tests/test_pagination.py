"""Tests for pagination on list endpoints."""


def test_tasks_pagination(client, seed_user):
    # Create several tasks
    for i in range(5):
        client.post("/tasks/", json={"task_type": "test", "title": f"Task {i}"})

    resp = client.get("/tasks/?limit=2&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) <= 2

    resp2 = client.get("/tasks/?limit=2&offset=2")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert len(data2) <= 2
    # Ensure different results (no overlap if enough data)
    if data and data2:
        assert data[0]["id"] != data2[0]["id"]


def test_memories_pagination(client, seed_user):
    for i in range(3):
        client.post("/memory/", json={
            "memory_type": "fact", "key": f"key{i}", "content": f"content{i}",
        })

    resp = client.get("/memory/?limit=1&offset=0")
    assert resp.status_code == 200
    assert len(resp.json()) <= 1


def test_approvals_filter_by_status(client, seed_user):
    resp = client.get("/approvals/?status=pending")
    assert resp.status_code == 200


def test_audit_logs_filter_by_event_type(client, seed_user):
    resp = client.get("/audit-logs/?event_type=action_requested")
    assert resp.status_code == 200


def test_audit_logs_pagination(client, seed_user):
    resp = client.get("/audit-logs/?limit=5&offset=0")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
