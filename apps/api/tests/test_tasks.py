def test_list_tasks(client):
    resp = client.get("/tasks/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_create_task(client, seed_user):
    resp = client.post("/tasks/", json={
        "user_id": 1,
        "task_type": "test_task",
        "title": "Integration test task",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Integration test task"
    assert data["status"] == "created"
    assert data["id"] is not None
