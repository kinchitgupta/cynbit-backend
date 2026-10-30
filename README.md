# Cynbit Backend Audit

Assessment project for the **Cynbit Technologies - Backend Developer Intern** role.

It has two parts:

| Part | What | Where |
|---|---|---|
| **A. Working backend** | A small FastAPI service demonstrating validation, persistence, error handling, rate limiting, duplicate-request prevention and tests | `app/`, `tests/` |
| **B. Technical audit** | Audit report, categorized security and performance findings, and recommended improvements about the public Cynbit website, from a backend developer's view | `docs/` |

> **Disclaimer.** This is an independent assessment project. It is **not** Cynbit's real
> backend, and the audit uses only publicly visible website content. Items described as
> "considerations" are general good practices, not claims that Cynbit has these problems.

## What the API does

The forms I observed on the public site (contact inquiry and programme registration) are
modelled as two small APIs:

| Method & path | Access | Purpose |
|---|---|---|
| `GET /health` | public | App + database health check |
| `POST /api/v1/inquiries` | public, rate limited, idempotent | Submit a contact inquiry |
| `GET /api/v1/inquiries` | admin | List inquiries (paginated) |
| `GET /api/v1/inquiries/{id}` | admin | Read one inquiry |
| `DELETE /api/v1/inquiries/{id}` | admin | Delete one inquiry |
| `POST /api/v1/enrollments` | public, rate limited, idempotent | Register for a programme lab |
| `GET /api/v1/enrollments` | admin | List registrations (paginated) |

"Admin" means sending the header `X-Admin-Key` (default `dev-admin-key` for local use).

## Features -> where to find them

| Feature | File | Tests |
|---|---|---|
| Input validation | `app/schemas.py` | `tests/test_inquiries.py`, `tests/test_enrollments.py` |
| Database operations (SQLite, parameterised SQL, constraints) | `app/database.py`, `app/routes.py` | all endpoint tests |
| Error handling (one JSON format, no leaked internals) | `app/errors.py` | `tests/test_health_and_errors.py` |
| Rate limiting (`429` + `Retry-After`) | `app/rate_limit.py` | `tests/test_rate_limit.py` |
| Duplicate-request prevention (`Idempotency-Key`) | `app/idempotency.py` | `tests/test_idempotency.py` |

## Run it

Requires Python 3.10+.

```bash
# 1. create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows PowerShell:  .venv\Scripts\Activate.ps1

# 2. install dependencies
pip install -r requirements.txt

# 3. start the server
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000/docs> for an interactive page where you can try every endpoint.

### Try it with curl

```bash
# create an inquiry (send the same Idempotency-Key twice: only one record is created)
curl -i -X POST http://127.0.0.1:8000/api/v1/inquiries \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: demo-key-0001" \
  -d '{"full_name":"Asha Verma","email":"asha@example.com","message":"I need a backend for my shop."}'

# read them back as admin
curl http://127.0.0.1:8000/api/v1/inquiries -H "X-Admin-Key: dev-admin-key"
```

Configuration (all optional environment variables): `CYNBIT_DB_PATH` (default `cynbit.db`),
`ADMIN_API_KEY` (default `dev-admin-key`; **change it for anything real**),
`RATE_LIMIT_MAX` (default 5) and `RATE_LIMIT_WINDOW` in seconds (default 60).

## Run the tests

```bash
pytest                   # run all tests
pytest --cov=app         # with coverage
```

Current result: **64 passed, 100% line coverage** of `app/`.

## Project layout

```
cynbit-backend-audit/
├── app/                      Backend application
│   ├── main.py               App setup, startup, /health
│   ├── routes.py             Endpoints
│   ├── schemas.py            Validation models
│   ├── database.py           SQLite schema and connections
│   ├── idempotency.py        Duplicate-request prevention
│   ├── rate_limit.py         Rate limiter
│   └── errors.py             Central error handling
├── tests/                    Automated tests (pytest)
├── docs/
│   ├── audit-report.md                 Deliverable 1: Backend Technical Audit Report
│   ├── security-performance-findings.md  Deliverable 2: categorized findings
│   ├── recommended-improvements.md     Deliverable 3: recommendations + code snippets
│   ├── website-observations.md         Evidence log (what was seen on public pages)
│   ├── api-observation-worksheet.md    Passive browser checks (headers, API shape)
│   └── design-decisions.md             Trade-offs, limitations, interview notes
├── requirements.txt
├── pytest.ini
└── .gitignore
```

## Known limitations

SQLite and an in-memory rate limiter keep the demo easy to run; a production system would use
PostgreSQL and Redis. There is no real authentication, payment or email integration. Details
in [`docs/design-decisions.md`](docs/design-decisions.md).

## Reading order for reviewers

1. This README  ->  2. `docs/audit-report.md`  ->  3. `docs/security-performance-findings.md`
->  4. `docs/recommended-improvements.md`  ->  5. `app/` (start with `routes.py`)  ->  6. `tests/`

Only passive, authorised analysis of public content was performed; nothing was exploited,
scanned, load-tested or submitted to Cynbit systems.
