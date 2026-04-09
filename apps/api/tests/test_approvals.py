def test_list_approvals(client):
    resp = client.get("/approvals/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_approve_nonexistent(client):
    resp = client.post("/approvals/99999/approve", json={"decision_notes": "test"})
    assert resp.status_code == 404


def test_reject_nonexistent(client):
    resp = client.post("/approvals/99999/reject", json={"decision_notes": "test"})
    assert resp.status_code == 404


def test_approve_flow(client, seed_user):
    # Create an action that requires approval
    resp = client.post("/actions/", json={
        "user_id": 1,
        "action_name": "create_file",
        "payload": {"relative_path": "restricted/approve-test.txt", "content": "test"},
    })
    assert resp.status_code == 200

    # Find the pending approval
    resp = client.get("/approvals/")
    approvals = [a for a in resp.json() if a["status"] == "pending"]
    assert len(approvals) > 0

    approval_id = approvals[0]["id"]

    # Approve it
    resp = client.post(f"/approvals/{approval_id}/approve", json={"decision_notes": "LGTM"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "approved"


def test_reject_flow(client, seed_user):
    # Create an action that requires approval
    resp = client.post("/actions/", json={
        "user_id": 1,
        "action_name": "create_file",
        "payload": {"relative_path": "restricted/reject-test.txt", "content": "test"},
    })
    assert resp.status_code == 200

    # Find pending approval
    resp = client.get("/approvals/")
    approvals = [a for a in resp.json() if a["status"] == "pending"]
    assert len(approvals) > 0

    approval_id = approvals[0]["id"]

    # Reject it
    resp = client.post(f"/approvals/{approval_id}/reject", json={"decision_notes": "Not now"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "rejected"


def test_double_approve_fails(client, seed_user):
    # Create an action that requires approval
    resp = client.post("/actions/", json={
        "user_id": 1,
        "action_name": "create_file",
        "payload": {"relative_path": "restricted/double-test.txt", "content": "test"},
    })

    resp = client.get("/approvals/")
    approvals = [a for a in resp.json() if a["status"] == "pending"]
    assert len(approvals) > 0

    approval_id = approvals[0]["id"]

    # Approve first
    resp = client.post(f"/approvals/{approval_id}/approve", json={"decision_notes": "ok"})
    assert resp.status_code == 200

    # Try approving again
    resp = client.post(f"/approvals/{approval_id}/approve", json={"decision_notes": "again"})
    assert resp.status_code == 400
