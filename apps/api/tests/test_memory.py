def test_list_memories(client):
    resp = client.get("/memory/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_create_memory(client, seed_user):
    resp = client.post("/memory/", json={
        "user_id": 1,
        "memory_type": "preference",
        "key": "test-key",
        "content": "Test memory content",
        "importance_score": 7,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["key"] == "test-key"
    assert data["content"] == "Test memory content"
    assert data["importance_score"] == 7
