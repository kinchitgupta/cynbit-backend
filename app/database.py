
import os
import sqlite3
from collections.abc import Iterator
from contextlib import closing

SCHEMA = """
CREATE TABLE IF NOT EXISTS inquiries (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name   TEXT NOT NULL,
    email       TEXT NOT NULL,
    company     TEXT,
    industry    TEXT,
    message     TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_inquiries_email ON inquiries(email);

CREATE TABLE IF NOT EXISTS enrollments (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name     TEXT NOT NULL,
    college       TEXT NOT NULL,
    email         TEXT NOT NULL,
    phone         TEXT NOT NULL,
    domain_lab    TEXT NOT NULL,
    referral_code TEXT,
    goals         TEXT,
    status        TEXT NOT NULL DEFAULT 'pending_payment',
    created_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    -- The database itself refuses a second enrollment for the same person in
    -- the same lab. Rules enforced in the DB cannot be bypassed by a bug or a
    -- race condition in application code.
    UNIQUE (email, domain_lab)
);

CREATE TABLE IF NOT EXISTS idempotency_keys (
    key           TEXT NOT NULL,
    endpoint      TEXT NOT NULL,
    fingerprint   TEXT NOT NULL,
    status_code   INTEGER NOT NULL,
    response_body TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    PRIMARY KEY (key, endpoint)
);
"""


def get_db_path() -> str:
    return os.getenv("CYNBIT_DB_PATH", "cynbit.db")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with closing(connect()) as conn:
        conn.executescript(SCHEMA)
        conn.commit()


def get_db() -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()
