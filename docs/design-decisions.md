# Design Decisions and Trade-offs

Short notes on *why* the demo is built the way it is. Useful for reviewers, and for me when
explaining the project.

## Decisions

| Decision | Why | Trade-off / what I'd change in production |
|---|---|---|
| **FastAPI + Pydantic** | Validation, typed models and auto-generated docs (`/docs`) come built in | None significant for this scale |
| **SQLite with raw SQL** | Zero setup so anyone can run it; raw parameterised SQL keeps the data layer easy to read and shows I understand injection safety | Move to PostgreSQL + SQLAlchemy/Alembic for migrations and concurrency |
| **Per-request DB connection** (`get_db` dependency) | No shared connection state between threads; always closed | Use a connection pool with PostgreSQL |
| **Idempotency keys are optional** | Not every client can send one; keeps the API easy to try | Make them mandatory for payment-related endpoints |
| **Key + body fingerprint** | Detects a client reusing a key with different data (a real bug class) | Add expiry (e.g. delete keys after 24 h) |
| **Record and saved response in one transaction** | Prevents "created but key not saved" states | - |
| **DB `UNIQUE(email, domain_lab)`** | Business rule enforced even if application code has a bug or a race | - |
| **In-memory sliding-window limiter** | Simple, no extra service, easy to unit-test with a fake clock | Shared Redis counters; read the real client IP from a trusted proxy header |
| **Rate limit on writes only** | Writes cost money (DB, email); reads here are admin-only | Add a looser limit on reads too |
| **`extra="forbid"` on inputs** | Stops mass-assignment (e.g. a client sending `status: paid`) | - |
| **Server controls `status`** | Payment state must never come from the browser | Set only by a verified payment webhook |
| **Shared admin key** | Smallest thing that protects personal data in a demo | Real auth: JWT/OAuth, roles, per-object checks, audit log |
| **One error format** | Front ends handle every failure identically; internals never leak | Add a request-ID to each error for support tracing |
| **Replay returns the original `201`** | Matches how payment APIs behave; the client cannot tell it apart except by the `Idempotent-Replay` header | - |

## Known limitations (stated deliberately)

- Rate-limit counters reset on restart and are not shared between server instances.
- The limiter's memory grows with the number of distinct client IPs (no eviction of idle clients).
- Idempotency keys never expire in this demo.
- No authentication beyond a shared key; no HTTPS termination, CORS policy or security headers
  (those belong to the deployment layer / a production hardening pass).
- Stored text is not HTML-escaped; escaping belongs at output time in whatever front end renders it.
- No payment or email integration.

## Questions I should be able to answer

1. **What happens if a user double-clicks submit?** Without a key two rows are created; with the same `Idempotency-Key` the second request replays the first response.
2. **What if two identical requests arrive at the same millisecond?** Both pass the first lookup; the database primary key lets one insert win; the other hits `IntegrityError`, re-reads the winner's saved response and returns it. The test `test_parallel_duplicate_is_replayed_not_duplicated` simulates exactly this.
3. **Why a 422 for a reused key with a different body?** The key promises "same request"; a different body means the client is buggy, and silently returning the old response would hide that.
4. **Why validate on the server when the form already validates?** Anyone can call the API directly, skipping the browser.
5. **How does parameterised SQL stop injection?** Values travel separately from the SQL text, so they can never be interpreted as SQL. There is a test storing `'); DROP TABLE...` as plain text.
6. **Why use `compare_digest` for the admin key?** It takes constant time, which blocks timing attacks that guess a secret character by character.
7. **What's wrong with the in-memory limiter at scale?** Each instance counts separately and restarts clear it; Redis `INCR` + `EXPIRE` is shared and atomic.
8. **Why does the 500 handler return a generic message?** Stack traces and SQL reveal internals to attackers; they are logged server-side instead.
9. **Why does 100% coverage not mean it's bug-free?** It proves every line ran, not that every input combination or concurrency scenario was tested.
10. **What would you add first with another week?** PostgreSQL + migrations, real authentication, Redis-backed limits, a worker queue for email, and CI.
