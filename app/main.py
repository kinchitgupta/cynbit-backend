
import logging
import sqlite3
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from app.database import get_db, init_db
from app.errors import AppError, register_exception_handlers
from app.routes import router

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Cynbit Backend Audit - Demo API",
    version="1.0.0",
    description=(
        "Independent assessment project demonstrating validation, persistence, "
        "error handling, rate limiting, idempotency keys and tests. "
        "Not Cynbit's real backend."
    ),
    lifespan=lifespan,
)

register_exception_handlers(app)
app.include_router(router)

@app.get("/health", tags=["system"])
def health(conn: sqlite3.Connection = Depends(get_db)) -> dict:
    try:
        conn.execute("SELECT 1")
    except sqlite3.Error:
        raise AppError(503, "database_unavailable", "Database is not reachable.") from None
    return {"status": "ok", "database": "ok"}
