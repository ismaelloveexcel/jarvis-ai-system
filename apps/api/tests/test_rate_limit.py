from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.testclient import TestClient

from app.main import app


def test_rate_limit_enforced():
    """Verify that exceeding the rate limit returns 429 on a rate-limited endpoint."""
    # Override the limiter with a very tight limit for this test
    original_limiter = app.state.limiter
    app.state.limiter = Limiter(key_func=get_remote_address, default_limits=["2/minute"])
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            # /actions/available is not exempt and does not require DB access
            responses = [client.get("/actions/available") for _ in range(5)]
    finally:
        app.state.limiter = original_limiter

    status_codes = [r.status_code for r in responses]
    assert 429 in status_codes, f"Expected a 429 rate-limit response, got: {status_codes}"
