import os
from unittest.mock import patch

from app.core.config import Settings


def test_no_api_key_allows_all(client):
    resp = client.get("/")
    assert resp.status_code in (200, 503)


def test_api_key_rejects_bad_key(client):
    with patch("app.core.auth.settings", Settings(API_KEY="real-key", RATE_LIMIT="1000/minute")):
        resp = client.post(
            "/chat/message",
            json={"content": "hi", "user_id": 1},
            headers={"X-API-Key": "wrong"},
        )
        assert resp.status_code == 401


def test_api_key_accepts_correct_key(client):
    with patch("app.core.auth.settings", Settings(API_KEY="real-key", RATE_LIMIT="1000/minute")):
        resp = client.get("/", headers={"X-API-Key": "real-key"})
        assert resp.status_code in (200, 503)


def test_blank_api_key_disables_auth(client):
    with patch("app.core.auth.settings", Settings(API_KEY="", RATE_LIMIT="1000/minute")):
        resp = client.get("/")
        assert resp.status_code in (200, 503)


def test_public_endpoints_bypass_auth(client):
    """/ and /health must be accessible even when API_KEY is set."""
    with patch("app.core.auth.settings", Settings(API_KEY="real-key", RATE_LIMIT="1000/minute")):
        resp = client.get("/")
        assert resp.status_code in (200, 503)

        resp = client.get("/health")
        assert resp.status_code in (200, 503)


def test_protected_endpoint_requires_key(client):
    """Non-public endpoints must return 401 when API_KEY is set and no key provided."""
    with patch("app.core.auth.settings", Settings(API_KEY="real-key", RATE_LIMIT="1000/minute")):
        resp = client.get("/tasks/")
        assert resp.status_code == 401

        resp = client.get("/approvals/")
        assert resp.status_code == 401
