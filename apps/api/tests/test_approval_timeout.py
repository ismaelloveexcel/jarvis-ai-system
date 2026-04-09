"""Tests for approval timeout/expiry."""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch


def test_approval_includes_expires_at(client, seed_user):
    """Approvals created via action should include expires_at."""
    resp = client.post("/actions/", json={
        "action_name": "create_file",
        "payload": {"relative_path": "secret/file.txt", "content": "x"},
    })
    assert resp.status_code == 200
    result = resp.json()["result"]
    assert result["status"] == "pending_approval"
    approval_id = result["approval_id"]

    approvals = client.get("/approvals/").json()
    approval = next(a for a in approvals if a["id"] == approval_id)
    assert approval["expires_at"] is not None


def test_expired_approval_rejected_on_approve(client, seed_user, db):
    """Attempting to approve an expired approval should return 410."""
    # Create an approval-requiring action
    resp = client.post("/actions/", json={
        "action_name": "create_file",
        "payload": {"relative_path": "secret/expired_test.txt", "content": "x"},
    })
    approval_id = resp.json()["result"]["approval_id"]

    # Manually expire the approval
    from app.models.approval import Approval
    approval = db.query(Approval).filter(Approval.id == approval_id).first()
    approval.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db.commit()

    # Try to approve it
    approve_resp = client.post(f"/approvals/{approval_id}/approve", json={"decision_notes": "too late"})
    assert approve_resp.status_code == 410


def test_approval_filter_pending(client, seed_user):
    """Filter approvals by status=pending."""
    resp = client.get("/approvals/?status=pending")
    assert resp.status_code == 200
    for a in resp.json():
        assert a["status"] == "pending"
