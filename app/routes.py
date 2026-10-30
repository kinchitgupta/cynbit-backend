import os
import secrets
import sqlite3

from fastapi import APIRouter, Depends, Header, Query, Response

from app.database import get_db
from app.errors import AppError
from app.idempotency import execute_once
from app.rate_limit import write_limiter
from app.schemas import EnrollmentCreate, EnrollmentOut, InquiryCreate, InquiryOut

router = APIRouter(prefix="/api/v1")


def require_admin(x_admin_key: str | None = Header(default=None)) -> None:
    expected = os.getenv("ADMIN_API_KEY", "dev-admin-key")
    if not x_admin_key or not secrets.compare_digest(x_admin_key.encode(), expected.encode()):
        raise AppError(401, "unauthorized", "A valid X-Admin-Key header is required.")


def idempotency_header(
    key: str | None = Header(default=None, alias="Idempotency-Key", min_length=8, max_length=128),
) -> str | None:

    return key


def _row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)



@router.post(
    "/inquiries",
    status_code=201,
    response_model=InquiryOut,
    dependencies=[Depends(write_limiter)],
)
def create_inquiry(
    payload: InquiryCreate,
    response: Response,
    conn: sqlite3.Connection = Depends(get_db),
    key: str | None = Depends(idempotency_header),
):
    def create(c: sqlite3.Connection) -> dict:
        cur = c.execute(
            "INSERT INTO inquiries (full_name, email, company, industry, message)"
            " VALUES (?, ?, ?, ?, ?)",
            (payload.full_name, payload.email, payload.company, payload.industry, payload.message),
        )
        row = c.execute("SELECT * FROM inquiries WHERE id = ?", (cur.lastrowid,)).fetchone()
        return _row_to_dict(row)

    return execute_once(
        conn,
        key=key,
        endpoint="POST /inquiries",
        payload=payload.model_dump(),
        create=create,
        response=response,
    )


@router.get("/inquiries", response_model=list[InquiryOut], dependencies=[Depends(require_admin)])
def list_inquiries(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    conn: sqlite3.Connection = Depends(get_db),
):
    rows = conn.execute(
        "SELECT * FROM inquiries ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset)
    ).fetchall()
    return [_row_to_dict(r) for r in rows]


@router.get(
    "/inquiries/{inquiry_id}", response_model=InquiryOut, dependencies=[Depends(require_admin)]
)
def get_inquiry(inquiry_id: int, conn: sqlite3.Connection = Depends(get_db)):
    row = conn.execute("SELECT * FROM inquiries WHERE id = ?", (inquiry_id,)).fetchone()
    if row is None:
        raise AppError(404, "not_found", "Inquiry not found.")
    return _row_to_dict(row)


@router.delete("/inquiries/{inquiry_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_inquiry(inquiry_id: int, conn: sqlite3.Connection = Depends(get_db)):
    with conn:
        cur = conn.execute("DELETE FROM inquiries WHERE id = ?", (inquiry_id,))
    if cur.rowcount == 0:
        raise AppError(404, "not_found", "Inquiry not found.")
    return Response(status_code=204)


@router.post(
    "/enrollments",
    status_code=201,
    response_model=EnrollmentOut,
    dependencies=[Depends(write_limiter)],
)
def create_enrollment(
    payload: EnrollmentCreate,
    response: Response,
    conn: sqlite3.Connection = Depends(get_db),
    key: str | None = Depends(idempotency_header),
):
    def create(c: sqlite3.Connection) -> dict:
        cur = c.execute(
            "INSERT INTO enrollments"
            " (full_name, college, email, phone, domain_lab, referral_code, goals)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                payload.full_name,
                payload.college,
                payload.email,
                payload.phone,
                payload.domain_lab.value,
                payload.referral_code,
                payload.goals,
            ),
        )
        row = c.execute("SELECT * FROM enrollments WHERE id = ?", (cur.lastrowid,)).fetchone()
        return _row_to_dict(row)

    try:
        return execute_once(
            conn,
            key=key,
            endpoint="POST /enrollments",
            payload=payload.model_dump(mode="json"),
            create=create,
            response=response,
        )
    except sqlite3.IntegrityError:
        raise AppError(
            409, "already_enrolled", "This email is already enrolled in the selected lab."
        ) from None


@router.get(
    "/enrollments", response_model=list[EnrollmentOut], dependencies=[Depends(require_admin)]
)
def list_enrollments(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    conn: sqlite3.Connection = Depends(get_db),
):
    rows = conn.execute(
        "SELECT * FROM enrollments ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset)
    ).fetchall()
    return [_row_to_dict(r) for r in rows]
