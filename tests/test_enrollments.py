"""Tests for the programme enrollment endpoint."""

import pytest


def test_create_enrollment_success(client, enrollment_payload):
    response = client.post("/api/v1/enrollments", json=enrollment_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["domain_lab"] == "python_backend"
    assert data["phone"] == "+919876543210"  # spaces removed by validation
    assert data["status"] == "pending_payment"  # server-controlled, not client-controlled


def test_client_cannot_set_status(client, enrollment_payload):
    enrollment_payload["status"] = "paid"
    assert client.post("/api/v1/enrollments", json=enrollment_payload).status_code == 422


def test_invalid_lab_is_rejected(client, enrollment_payload):
    enrollment_payload["domain_lab"] = "hacking_101"
    response = client.post("/api/v1/enrollments", json=enrollment_payload)
    assert response.status_code == 422


@pytest.mark.parametrize("phone", ["12345", "abcdefghij", "+91-98765-4321x", pytest.param("1" * 20, id="too-many-digits")])
def test_invalid_phone_is_rejected(client, enrollment_payload, phone):
    enrollment_payload["phone"] = phone
    response = client.post("/api/v1/enrollments", json=enrollment_payload)
    assert response.status_code == 422


@pytest.mark.parametrize("phone", ["9876543210", "+91 98765 43210", "(+91) 98765-43210"])
def test_common_phone_formats_are_accepted(client, enrollment_payload, phone):
    enrollment_payload["phone"] = phone
    assert client.post("/api/v1/enrollments", json=enrollment_payload).status_code == 201


def test_same_person_cannot_enrol_twice_in_same_lab(client, enrollment_payload):
    assert client.post("/api/v1/enrollments", json=enrollment_payload).status_code == 201
    duplicate = client.post("/api/v1/enrollments", json=enrollment_payload)
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "already_enrolled"


def test_email_case_does_not_bypass_duplicate_check(client, enrollment_payload):
    client.post("/api/v1/enrollments", json=enrollment_payload)
    enrollment_payload["email"] = "ROHIT@EXAMPLE.COM"
    assert client.post("/api/v1/enrollments", json=enrollment_payload).status_code == 409


def test_same_person_can_join_a_different_lab(client, enrollment_payload):
    client.post("/api/v1/enrollments", json=enrollment_payload)
    enrollment_payload["domain_lab"] = "ai_vector"
    assert client.post("/api/v1/enrollments", json=enrollment_payload).status_code == 201


def test_admin_can_list_enrollments(client, admin, enrollment_payload):
    assert client.get("/api/v1/enrollments").status_code == 401
    client.post("/api/v1/enrollments", json=enrollment_payload)
    rows = client.get("/api/v1/enrollments", headers=admin).json()
    assert len(rows) == 1
    assert rows[0]["email"] == "rohit@example.com"
