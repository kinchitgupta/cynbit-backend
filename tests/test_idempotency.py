"""Tests for duplicate-request prevention (Idempotency-Key header)."""

from contextlib import closing

KEY = "11111111-2222-3333-4444-555555555555"


def count_inquiries(client, admin):
    return len(client.get("/api/v1/inquiries", headers=admin).json())


def test_same_key_same_body_creates_only_one_record(client, admin, inquiry_payload):
    first = client.post("/api/v1/inquiries", json=inquiry_payload, headers={"Idempotency-Key": KEY})
    second = client.post("/api/v1/inquiries", json=inquiry_payload, headers={"Idempotency-Key": KEY})

    assert first.status_code == 201
    assert second.status_code == 201
    assert second.json() == first.json()  # exactly the same saved response
    assert "idempotent-replay" not in first.headers
    assert second.headers["Idempotent-Replay"] == "true"
    assert count_inquiries(client, admin) == 1  # <- the whole point


def test_same_key_different_body_is_rejected(client, admin, inquiry_payload):
    client.post("/api/v1/inquiries", json=inquiry_payload, headers={"Idempotency-Key": KEY})
    inquiry_payload["message"] = "A completely different message than before."
    response = client.post("/api/v1/inquiries", json=inquiry_payload, headers={"Idempotency-Key": KEY})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "idempotency_key_reused"
    assert count_inquiries(client, admin) == 1


def test_different_keys_create_separate_records(client, admin, inquiry_payload):
    client.post("/api/v1/inquiries", json=inquiry_payload, headers={"Idempotency-Key": KEY})
    client.post("/api/v1/inquiries", json=inquiry_payload, headers={"Idempotency-Key": KEY + "-b"})
    assert count_inquiries(client, admin) == 2


def test_without_a_key_requests_are_not_deduplicated(client, admin, inquiry_payload):
    client.post("/api/v1/inquiries", json=inquiry_payload)
    client.post("/api/v1/inquiries", json=inquiry_payload)
    assert count_inquiries(client, admin) == 2


def test_too_short_key_is_rejected(client, inquiry_payload):
    response = client.post("/api/v1/inquiries", json=inquiry_payload, headers={"Idempotency-Key": "abc"})
    assert response.status_code == 422


def test_key_is_scoped_per_endpoint(client, admin, inquiry_payload, enrollment_payload):
    """The same key value on two different endpoints must not collide."""
    ok1 = client.post("/api/v1/inquiries", json=inquiry_payload, headers={"Idempotency-Key": KEY})
    ok2 = client.post("/api/v1/enrollments", json=enrollment_payload, headers={"Idempotency-Key": KEY})
    assert ok1.status_code == 201
    assert ok2.status_code == 201


def test_enrollment_retry_with_key_replays_instead_of_409(client, admin, enrollment_payload):
    """A retried request with the same key is a replay (201), while a NEW
    attempt without it is correctly rejected as a duplicate (409)."""
    first = client.post("/api/v1/enrollments", json=enrollment_payload, headers={"Idempotency-Key": KEY})
    retry = client.post("/api/v1/enrollments", json=enrollment_payload, headers={"Idempotency-Key": KEY})
    fresh_attempt = client.post("/api/v1/enrollments", json=enrollment_payload)

    assert first.status_code == 201
    assert retry.status_code == 201
    assert retry.json() == first.json()
    assert fresh_attempt.status_code == 409
    assert len(client.get("/api/v1/enrollments", headers=admin).json()) == 1


def test_parallel_duplicate_is_replayed_not_duplicated(client, admin, inquiry_payload, monkeypatch):
    """Simulates the race: two identical requests pass the first 'have I seen
    this key?' check at the same moment. The database PRIMARY KEY lets only one
    insert succeed; the loser must replay the winner's response."""
    import app.idempotency as idem
    from app.database import connect

    # Request A completes normally first.
    winner = client.post("/api/v1/inquiries", json=inquiry_payload, headers={"Idempotency-Key": KEY})

    # Request B "didn't see" A's key on its first lookup (the race window).
    real_lookup = idem._lookup
    calls = {"n": 0}

    def blind_first_lookup(conn, key, endpoint, fp):
        calls["n"] += 1
        return None if calls["n"] == 1 else real_lookup(conn, key, endpoint, fp)

    monkeypatch.setattr(idem, "_lookup", blind_first_lookup)
    loser = client.post("/api/v1/inquiries", json=inquiry_payload, headers={"Idempotency-Key": KEY})

    assert loser.status_code == 201
    assert loser.json() == winner.json()
    assert loser.headers["Idempotent-Replay"] == "true"
    assert count_inquiries(client, admin) == 1  # the loser's INSERT was rolled back
    with closing(connect()) as conn:
        assert conn.execute("SELECT COUNT(*) FROM inquiries").fetchone()[0] == 1


def test_business_rule_failure_with_key_is_409_and_key_is_not_saved(client, admin, enrollment_payload):
    """If the INSERT itself is refused (duplicate enrolment), the idempotency
    key must NOT be stored - the failed attempt is rolled back entirely."""
    client.post("/api/v1/enrollments", json=enrollment_payload)  # already enrolled
    rejected = client.post("/api/v1/enrollments", json=enrollment_payload, headers={"Idempotency-Key": KEY})
    assert rejected.status_code == 409

    from app.database import connect

    with closing(connect()) as conn:
        assert conn.execute("SELECT COUNT(*) FROM idempotency_keys").fetchone()[0] == 0
