# Security & Performance Findings

**Deliverable 2 of 3** · Backend Developer Intern assessment · Cynbit Technologies
**Date:** 31 October 2026 · **Method:** passive review of public page content only

## How to read this

Every finding carries an **evidence tag**, so you can tell fact from opinion:

| Tag | Meaning |
|---|---|
| **Observed** | Stated or visible on a public page |
| **Inferred** | A reasonable conclusion from observed facts; not confirmed |
| **Consideration** | A good practice that applies to a site with these features. **Not a claim that Cynbit lacks it** |
| **To verify** | Needs browser-based passive checks (see `api-observation-worksheet.md`) |

**Priority** = importance *if the practice is absent*: **High / Medium / Low**.

No exploitation, scanning, load testing or form submission was performed. I could not
inspect response headers or network traffic from page text, so several items below are
deliberately marked **To verify** rather than asserted.

## Summary

| Category | Findings | High | Medium | Low |
|---|---|---|---|---|
| Security | 5 | 3 | 2 | 0 |
| Authentication & authorisation | 3 | 2 | 1 | 0 |
| Data validation & handling | 3 | 2 | 1 | 0 |
| Performance | 4 | 0 | 3 | 1 |
| Error handling & reliability | 2 | 0 | 2 | 0 |
| Architecture & observability | 2 | 0 | 1 | 1 |

---

## 1. Security

| ID | Finding | Evidence | Priority | Recommendation |
|---|---|---|---|---|
| S1 | **Abuse protection on public forms.** Contact, demo-request, newsletter and registration forms are open to anonymous traffic. Without per-client rate limits and a bot check, spam can flood the lead list and exhaust the email quota | Consideration (forms Observed) | High | Rate limit by IP + email; add CAPTCHA or a honeypot field. Demo: `app/rate_limit.py` |
| S2 | **Payment confirmation integrity.** Registration is followed by a Cashfree payment, after which accounts are created and credentials emailed. If "paid" were decided from the browser redirect, it could be forged | Consideration (payment flow Observed) | High | Trust only the gateway's signed server-to-server webhook; verify signature, process each event once, reconcile with the gateway API. See `recommended-improvements.md` §4 |
| S3 | **Credential delivery by email.** The page says credentials are sent to the registration email. If that means a password in plain text, email is a weak channel | Observed text; mechanism **To verify** | High | Send a single-use, short-lived "set your password" link instead |
| S4 | **Security response headers.** Whether HSTS, CSP, `X-Content-Type-Options` and `Referrer-Policy` are set cannot be seen from page text | To verify | Medium | Check in DevTools; if missing, add via `next.config.js` (see `recommended-improvements.md` §1) |
| S5 | **Third-party data processors.** Resend (email), Prisma (database layer) and Cashfree (payments) each handle personal data | Observed | Medium | Keep an inventory of processors, restrict API keys to least privilege, store secrets in environment/secret manager, rotate periodically |

## 2. Authentication & authorisation

| ID | Finding | Evidence | Priority | Recommendation |
|---|---|---|---|---|
| A1 | **Per-object authorisation.** The intern portal (own tasks, PR links, certificates) and Revio (Admin/Manager/Advisor, multiple locations) imply data that must be isolated per user or tenant. Hiding UI buttons is not access control | Consideration (portal and roles Observed) | High | Enforce checks on the server for every object read/write (`WHERE owner_id = :me`); add tests that user A cannot fetch user B's record (IDOR) |
| A2 | **Public certificate verification.** Certificates carry a public QR check. If identifiers are sequential, anyone can enumerate other people's certificates | Consideration (QR check Observed) | High | Use unguessable IDs (UUIDv4 or signed tokens), return minimal data, rate limit lookups |
| A3 | **Session and login hardening** for the portal: brute-force protection, secure/HttpOnly/SameSite cookies, short-lived tokens | To verify (portal is behind login, not inspected) | Medium | Lockout or progressive delay after failed attempts; cookie flags; refresh-token rotation |

## 3. Data validation & handling

| ID | Finding | Evidence | Priority | Recommendation |
|---|---|---|---|---|
| D1 | **Server-side validation on every form.** Browser checks are bypassable. Fields like phone, email, college and free-text messages need length, format and allowed-value checks, and unknown fields should be rejected | Consideration (fields Observed) | High | Schema validation (zod in Next.js, Pydantic in FastAPI). Demo: `app/schemas.py` |
| D2 | **Duplicate submissions.** Double-clicks and retries can create duplicate leads or enrolments, and duplicate payment orders | Consideration | High | Idempotency keys + DB unique constraints. Demo: `app/idempotency.py` |
| D3 | **Privacy policy vs actual data flows.** The policy (updated 20 May 2026) names the email and database partners and mentions inquiry forms and BitElevate applications; the site also uses a payment gateway and a newsletter list | Observed | Medium | Align the policy with real processors; define retention periods; make the deletion-on-request process auditable. Review with qualified counsel (India's DPDP Act, 2023) |

## 4. Performance

| ID | Finding | Evidence | Priority | Recommendation |
|---|---|---|---|---|
| P1 | **Oversized image requests.** Student photos on `/bitelevate` are requested through the Next.js image optimiser at `w=3840`, far above what a small avatar needs | Observed in image URLs; delivered size **To verify** | Medium | Set accurate `sizes` on the image component so avatars request ~64-128 px variants (`recommended-improvements.md` §5) |
| P2 | **Static page caching.** Marketing pages are largely static; whether they are cached at the edge cannot be seen from page text | To verify | Medium | Static generation/ISR plus CDN caching; long-lived immutable caching for hashed assets |
| P3 | **Repeated blocks.** The testimonial section appears to render its cards twice (typical of a looping marquee), increasing DOM size and images loaded | Observed (duplicated content in the page text) | Low | Lazy-load off-screen images; consider a CSS-only loop that does not duplicate heavy content |
| P4 | **Database growth and query cost** as leads, enrolments, task submissions and reviews grow | Consideration | Medium | Index lookup columns (email, owner_id, status); paginate admin lists; cache hot reads in Redis |

## 5. Error handling & reliability

| ID | Finding | Evidence | Priority | Recommendation |
|---|---|---|---|---|
| E1 | **Email delivery in the request path.** If the form handler waits for the email API, a provider slowdown makes the form slow or fail even though the data was saved | Consideration | Medium | Save first, queue the email, retry with back-off; surface failures in logs. Demo architecture in `audit-report.md` §6 |
| E2 | **Consistent, safe error responses.** Errors should share one JSON shape and never expose stack traces or SQL | Consideration | Medium | Central handlers. Demo: `app/errors.py`, `tests/test_health_and_errors.py` |

## 6. Architecture & observability

| ID | Finding | Evidence | Priority | Recommendation |
|---|---|---|---|---|
| R1 | **Uptime claim needs measurement.** The services page cites 99.9% uptime | Observed claim | Medium | Health checks, structured logs with request IDs, error tracking, alerts, a public status page |
| R2 | **Metadata consistency.** Several pages declare the homepage as `og:url`, and the apex and `www` hosts are mixed. Relevant since technical SEO is a listed service | Observed | Low | One canonical host with 301 redirect; per-page canonical URL and `og:url` |

---

## Items for AI/LLM features (Consideration)

Cynbit Studio advertises AI code evaluation, mock interviews and AI-assisted review replies in
Revio. If these call third-party models or run user-submitted code on the server:

- sandbox any code execution (isolated container, no network, CPU/memory/time limits);
- apply per-user quotas and spend caps; use timeouts, retries and circuit breakers;
- treat model input as untrusted (prompt injection) and avoid sending unnecessary personal data;
- require human approval before AI replies are posted publicly.
