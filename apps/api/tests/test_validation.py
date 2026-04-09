"""Tests for input validation (Field constraints, Pydantic models)."""


def test_empty_title_rejected(client, seed_user):
    resp = client.post("/tasks/", json={"task_type": "test", "title": ""})
    assert resp.status_code == 422


def test_empty_chat_content_rejected(client, seed_user):
    resp = client.post("/chat/message", json={"content": ""})
    assert resp.status_code == 422


def test_invalid_user_id_rejected(client, seed_user):
    resp = client.post("/tasks/", json={"task_type": "test", "title": "ok", "user_id": 0})
    assert resp.status_code == 422


def test_memory_importance_out_of_range(client, seed_user):
    resp = client.post("/memory/", json={
        "memory_type": "fact", "key": "k", "content": "c", "importance_score": 99,
    })
    assert resp.status_code == 422


def test_memory_importance_below_range(client, seed_user):
    resp = client.post("/memory/", json={
        "memory_type": "fact", "key": "k", "content": "c", "importance_score": 0,
    })
    assert resp.status_code == 422


def test_action_empty_name_rejected(client, seed_user):
    resp = client.post("/actions/", json={"action_name": "", "payload": {}})
    assert resp.status_code == 422


def test_get_task_by_id(client, seed_user):
    create = client.post("/tasks/", json={"task_type": "test", "title": "Detail test"})
    assert create.status_code == 200
    task_id = create.json()["id"]

    resp = client.get(f"/tasks/{task_id}")
    assert resp.status_code == 200
    assert resp.json()["task_id"] == task_id


def test_get_task_not_found(client, seed_user):
    resp = client.get("/tasks/99999")
    assert resp.status_code == 404
