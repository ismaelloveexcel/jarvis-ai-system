"""Tests for memory CRUD (GET/PUT/DELETE)."""


def test_memory_get_by_id(client, seed_user):
    create = client.post("/memory/", json={
        "memory_type": "fact", "key": "test_get", "content": "Get me",
    })
    assert create.status_code == 200
    memory_id = create.json()["id"]

    resp = client.get(f"/memory/{memory_id}")
    assert resp.status_code == 200
    assert resp.json()["content"] == "Get me"


def test_memory_get_not_found(client, seed_user):
    resp = client.get("/memory/99999")
    assert resp.status_code == 404


def test_memory_update(client, seed_user):
    create = client.post("/memory/", json={
        "memory_type": "fact", "key": "test_update", "content": "Original",
    })
    memory_id = create.json()["id"]

    resp = client.put(f"/memory/{memory_id}", json={"content": "Updated", "importance_score": 9})
    assert resp.status_code == 200
    assert resp.json()["content"] == "Updated"
    assert resp.json()["importance_score"] == 9


def test_memory_delete(client, seed_user):
    create = client.post("/memory/", json={
        "memory_type": "fact", "key": "test_delete", "content": "Delete me",
    })
    memory_id = create.json()["id"]

    resp = client.delete(f"/memory/{memory_id}")
    assert resp.status_code == 204

    get_resp = client.get(f"/memory/{memory_id}")
    assert get_resp.status_code == 404


def test_memory_delete_not_found(client, seed_user):
    resp = client.delete("/memory/99999")
    assert resp.status_code == 404


def test_memory_filter_by_type(client, seed_user):
    client.post("/memory/", json={
        "memory_type": "preference", "key": "theme", "content": "dark",
    })
    resp = client.get("/memory/?memory_type=preference")
    assert resp.status_code == 200
    for m in resp.json():
        assert m["memory_type"] == "preference"
