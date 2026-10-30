"""Tests for the inquiry endpoints: validation, storage, admin access."""

import pytest


# ------------------------------------------------------------ happy path


def test_create_inquiry_success(client, inquiry_payload):
    response = client.post("/api/v1/inquiries", json=inquiry_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["full_name"] == "Asha Verma"
    assert data["email"] == "asha@example.com"  # lower-cased by validation
    assert data["created_at"]  # timestamp filled in by the database


def test_blank_optional_fields_are_stored_as_null(client, inquiry_payload):
    inquiry_payload["company"] = "   "
    inquiry_payload["industry"] = ""
    data = client.post("/api/v1/inquiries", json=inquiry_payload).json()
    assert data["company"] is None
    assert data["industry"] is None


def test_optional_fields_can_be_omitted(client, inquiry_payload):
    del inquiry_payload["company"]
    del inquiry_payload["industry"]
    assert client.post("/api/v1/inquiries", json=inquiry_payload).status_code == 201


def test_surrounding_whitespace_is_trimmed(client, inquiry_payload):
    inquiry_payload["full_name"] = "   Asha Verma   "
    data = client.post("/api/v1/inquiries", json=inquiry_payload).json()
    assert data["full_name"] == "Asha Verma"


# ------------------------------------------------------------ validation


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("full_name", "A"),  # too short
        pytest.param("full_name", "X" * 101, id="name-too-long"),
        ("full_name", "<script>alert(1)</script>"),  # illegal characters
        ("full_name", "Robert'); DROP TABLE inquiries;--"),  # illegal characters
        ("email", "not-an-email"),
        ("email", "missing@domain"),
        ("message", "too short"),  # < 10 characters
        pytest.param("message", "M" * 2001, id="message-too-long"),
        pytest.param("company", "C" * 121, id="company-too-long"),
    ],
)
def test_invalid_input_is_rejected(client, inquiry_payload, field, bad_value):
    inquiry_payload[field] = bad_value
    response = client.post("/api/v1/inquiries", json=inquiry_payload)
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    # The error points at the offending field so a form can highlight it.
    assert any(d["field"] == field for d in body["error"]["details"])


@pytest.mark.parametrize("missing", ["full_name", "email", "message"])
def test_required_fields_are_enforced(client, inquiry_payload, missing):
    del inquiry_payload[missing]
    response = client.post("/api/v1/inquiries", json=inquiry_payload)
    assert response.status_code == 422


def test_unknown_fields_are_rejected(client, inquiry_payload):
    inquiry_payload["is_admin"] = True  # a "mass assignment" attempt
    response = client.post("/api/v1/inquiries", json=inquiry_payload)
    assert response.status_code == 422


def test_sql_injection_text_is_stored_harmlessly(client, admin, inquiry_payload):
    """Because queries are parameterised, SQL in the message is just text."""
    inquiry_payload["message"] = "'); DROP TABLE inquiries; -- hello there"
    assert client.post("/api/v1/inquiries", json=inquiry_payload).status_code == 201
    # The table still exists and the text came back unchanged.
    rows = client.get("/api/v1/inquiries", headers=admin).json()
    assert len(rows) == 1
    assert rows[0]["message"] == "'); DROP TABLE inquiries; -- hello there"


# ---------------------------------------------------------- admin access


def test_listing_requires_admin_key(client):
    response = client.get("/api/v1/inquiries")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_wrong_admin_key_is_rejected(client):
    response = client.get("/api/v1/inquiries", headers={"X-Admin-Key": "wrong"})
    assert response.status_code == 401


def test_non_ascii_admin_key_does_not_crash(client):
    response = client.get("/api/v1/inquiries", headers={"X-Admin-Key": "kéy".encode("utf-8")})
    assert response.status_code == 401


def test_admin_can_list_with_pagination(client, admin, inquiry_payload):
    for i in range(3):
        inquiry_payload["message"] = f"Message number {i} for pagination test"
        client.post("/api/v1/inquiries", json=inquiry_payload)

    everything = client.get("/api/v1/inquiries", headers=admin).json()
    assert [r["id"] for r in everything] == [3, 2, 1]  # newest first

    page = client.get("/api/v1/inquiries?limit=1&offset=1", headers=admin).json()
    assert [r["id"] for r in page] == [2]


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "offset=-1", "limit=abc"])
def test_bad_pagination_values_are_rejected(client, admin, query):
    response = client.get(f"/api/v1/inquiries?{query}", headers=admin)
    assert response.status_code == 422


def test_get_single_inquiry_and_404(client, admin, inquiry_payload):
    client.post("/api/v1/inquiries", json=inquiry_payload)
    assert client.get("/api/v1/inquiries/1", headers=admin).status_code == 200
    missing = client.get("/api/v1/inquiries/999", headers=admin)
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "not_found"


def test_non_numeric_id_is_422(client, admin):
    assert client.get("/api/v1/inquiries/abc", headers=admin).status_code == 422


def test_delete_inquiry(client, admin, inquiry_payload):
    client.post("/api/v1/inquiries", json=inquiry_payload)
    assert client.delete("/api/v1/inquiries/1").status_code == 401  # needs admin
    assert client.delete("/api/v1/inquiries/1", headers=admin).status_code == 204
    assert client.get("/api/v1/inquiries/1", headers=admin).status_code == 404
    assert client.delete("/api/v1/inquiries/1", headers=admin).status_code == 404
