"""Shared test setup (pytest "fixtures").

A fixture is a helper that pytest prepares before a test and hands to it by
name. These ones guarantee every test starts from a clean slate, so tests
never affect each other.
"""

import pytest
from fastapi.testclient import TestClient

from app.database import init_db
from app.main import app
from app.rate_limit import write_limiter

ADMIN_KEY = "test-admin-key"


@pytest.fixture(autouse=True)  # autouse=True -> applied to EVERY test automatically
def clean_environment(tmp_path, monkeypatch):
    """Give each test its own empty database file and a reset rate limiter."""
    monkeypatch.setenv("CYNBIT_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("ADMIN_API_KEY", ADMIN_KEY)
    init_db()
    write_limiter.reset()
    yield
    write_limiter.reset()


@pytest.fixture
def client():
    """A fake browser that calls the API in-process (no real server needed)."""
    return TestClient(app)


@pytest.fixture
def admin():
    """Headers that identify the caller as an admin."""
    return {"X-Admin-Key": ADMIN_KEY}


@pytest.fixture
def inquiry_payload():
    """A valid inquiry body; tests copy and tweak it."""
    return {
        "full_name": "Asha Verma",
        "email": "Asha@Example.com",
        "company": "Verma Traders",
        "industry": "Retail",
        "message": "We would like a quote for a small inventory web app.",
    }


@pytest.fixture
def enrollment_payload():
    return {
        "full_name": "Rohit Sharma",
        "college": "SKIT Jaipur",
        "email": "rohit@example.com",
        "phone": "+91 98765 43210",
        "domain_lab": "python_backend",
        "goals": "Become a backend engineer.",
    }
