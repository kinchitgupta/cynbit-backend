import hashlib
import json
import sqlite3
from collections.abc import Callable

from fastapi import Response

from app.errors import AppError


def fingerprint(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _lookup(conn: sqlite3.Connection, key: str, endpoint: str, fp: str) -> dict | None:
    row = conn.execute(
        "SELECT fingerprint, response_body FROM idempotency_keys WHERE key = ? AND endpoint = ?",
        (key, endpoint),
    ).fetchone()
    if row is None:
        return None
    if row["fingerprint"] != fp:
        raise AppError(
            status_code=422,
            code="idempotency_key_reused",
            message="This Idempotency-Key was already used with a different request body.",
        )
    return json.loads(row["response_body"])

def execute_once(
    conn: sqlite3.Connection,
    *,
    key: str | None,
    endpoint: str,
    payload: dict,
    create: Callable[[sqlite3.Connection], dict],
    response: Response,
) -> dict:

    if key is None:
        with conn:
            return create(conn)
    fp = fingerprint(payload)
    saved = _lookup(conn, key, endpoint, fp)
    if saved is not None:
        response.headers["Idempotent-Replay"] = "true"
        return saved
    try:
        with conn:
            body = create(conn)
            conn.execute(
                "INSERT INTO idempotency_keys (key, endpoint, fingerprint, status_code, response_body)"
                " VALUES (?, ?, ?, ?, ?)",
                (key, endpoint, fp, 201, json.dumps(body)),
            )
        return body
    except sqlite3.IntegrityError:
        saved = _lookup(conn, key, endpoint, fp)
        if saved is not None:
            response.headers["Idempotent-Replay"] = "true"
            return saved
        raise
