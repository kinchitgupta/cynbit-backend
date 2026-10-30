"""Tests for rate limiting."""

from types import SimpleNamespace

import pytest

from app.errors import AppError
from app.rate_limit import RateLimiter


def test_sixth_request_in_a_minute_is_blocked(client, inquiry_payload):
    # The default limit is 5 write requests per 60 seconds per client.
    for _ in range(5):
        assert client.post("/api/v1/inquiries", json=inquiry_payload).status_code == 201

    blocked = client.post("/api/v1/inquiries", json=inquiry_payload)
    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "rate_limited"
    # Retry-After tells well-behaved clients how many seconds to wait.
    assert 1 <= int(blocked.headers["Retry-After"]) <= 60


def test_limit_is_shared_by_all_write_endpoints(client, inquiry_payload, enrollment_payload):
    for _ in range(5):
        client.post("/api/v1/inquiries", json=inquiry_payload)
    assert client.post("/api/v1/enrollments", json=enrollment_payload).status_code == 429


def test_read_endpoints_and_health_are_not_limited(client, admin):
    for _ in range(10):
        assert client.get("/health").status_code == 200
        assert client.get("/api/v1/inquiries", headers=admin).status_code == 200


# --- unit tests of the limiter itself, with a fake clock ----------------------


def fake_request(ip="1.2.3.4"):
    """Minimal stand-in for a FastAPI Request (only .client.host is used)."""
    return SimpleNamespace(client=SimpleNamespace(host=ip))


def test_window_expires_and_requests_are_allowed_again(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr("app.rate_limit.time.monotonic", lambda: now[0])

    limiter = RateLimiter(max_requests=2, window_seconds=10)
    limiter(fake_request())
    limiter(fake_request())
    with pytest.raises(AppError) as blocked:
        limiter(fake_request())
    assert blocked.value.status_code == 429

    now[0] += 10.1  # time passes beyond the window
    limiter(fake_request())  # allowed again, no exception


def test_each_client_has_its_own_budget():
    limiter = RateLimiter(max_requests=1, window_seconds=60)
    limiter(fake_request("10.0.0.1"))
    limiter(fake_request("10.0.0.2"))  # different client: not affected
    with pytest.raises(AppError):
        limiter(fake_request("10.0.0.1"))
