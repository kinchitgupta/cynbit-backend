"""Tests for the health check and the centralised error handling."""

from fastapi.testclient import TestClient

from app.main import app


def test_health_reports_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_unknown_url_returns_standard_error_shape(client):
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "http_error"


def test_wrong_http_method_returns_405(client):
    response = client.put("/api/v1/inquiries")
    assert response.status_code == 405
    assert "error" in response.json()


def test_malformed_json_is_a_clean_422(client):
    response = client.post(
        "/api/v1/inquiries",
        content="{not valid json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


# --- unexpected crashes must NOT leak internal details -------------------------


@app.get("/__test_boom__", include_in_schema=False)
def _boom():
    # A route that crashes on purpose, registered only for this test file.
    raise RuntimeError("secret internal detail: db password is hunter2")


def test_unexpected_exception_returns_generic_500_without_leaking_details():
    # raise_server_exceptions=False makes TestClient behave like a real
    # client: it receives the 500 response instead of seeing the Python error.
    safe_client = TestClient(app, raise_server_exceptions=False)
    response = safe_client.get("/__test_boom__")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    assert "hunter2" not in response.text
    assert "RuntimeError" not in response.text


def test_startup_creates_tables_automatically(tmp_path, monkeypatch):
    """Using TestClient as a context manager runs the app's startup hook."""
    monkeypatch.setenv("CYNBIT_DB_PATH", str(tmp_path / "fresh.db"))
    with TestClient(app) as started:  # triggers lifespan -> init_db()
        assert started.get("/health").status_code == 200


def test_health_returns_503_when_database_is_down():
    import sqlite3

    from app.database import get_db

    class BrokenConnection:
        def execute(self, *_):
            raise sqlite3.OperationalError("disk I/O error")

    app.dependency_overrides[get_db] = lambda: BrokenConnection()
    try:
        response = TestClient(app).get("/health")
    finally:
        app.dependency_overrides.clear()  # always undo the override
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "database_unavailable"
