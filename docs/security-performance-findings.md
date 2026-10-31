# Security & Performance Findings
 
**Deliverable 2 of 3** · Backend Developer Intern assessment · Cynbit Technologies
**Date:** 31 October 2026 · **Method:** passive review of public page content, plus one normal page load observed in Chrome DevTools (response headers and page HTML of `/contact`)
 
## How to read this
 
Every finding carries an **evidence tag**, so you can tell fact from opinion:
 
| Tag | Meaning |
|---|---|
| **Observed** | Stated or visible on a public page, or seen in the browser's own network panel |
| **Inferred** | A reasonable conclusion from observed facts; not confirmed |
| **Consideration** | A good practice that applies to a site with these features. **Not a claim that Cynbit lacks it** |
| **To verify** | Could not be checked passively from what I had |
 
**Priority** = importance *if the practice is absent*: **High / Medium / Low**.
 
No exploitation, scanning, load testing or form submission was performed. Response headers were read from the same page load a visitor makes. Where a protection might exist but would not show up in the page HTML or headers (for example a server-side rate limit), the finding is a **Consideration**, not a claim.
 
## Summary
 
| Category | Findings | High | Medium | Low |
|---|---|---|---|---|
| Security | 6 | 3 | 2 | 1 |
| Authentication & authorisation | 3 | 2 | 1 | 0 |
| Data validation & handling | 3 | 2 | 1 | 0 |
| Performance | 6 | 0 | 3 | 3 |
| Error handling & reliability | 2 | 0 | 2 | 0 |
| Architecture & observability | 2 | 0 | 1 | 1 |
| **Total** | **22** | **7** | **10** | **5** |
 
## What is already done well (observed)
 
| Strength | Evidence |
|---|---|
| HTTPS is enforced for browsers with a long HSTS lifetime | `strict-transport-security: max-age=63072000` (2 years) |
| Pages are compressed | `content-encoding: br` (Brotli); the contact page HTML transfers at about 11 kB |
| Static pages are served from an edge cache | `x-vercel-cache: HIT`, `x-nextjs-prerender: 1` |
| Conditional requests are supported | `etag` header present; the document revalidated with HTTP 304 |
| Structured data for search engines | JSON-LD `ContactPage` and `ProfessionalService` blocks in the HTML |
| Few third-party scripts on the contact page | Only Google Tag and Google Fonts appear in the HTML |
| A privacy policy exists with a data-deletion route | `/privacy`, updated 20 May 2026 |
| Basic browser-side form checks | `required` on name, email and message; `type="email"` on email |
 
---
 
## 1. Security
 
| ID | Finding | Evidence | Priority | Recommendation |
|---|---|---|---|---|
| S1 | **Abuse protection on public forms.** The contact form has no CAPTCHA, honeypot field or CSRF token in its HTML. A server-side rate limit would not be visible from outside, so I cannot say whether one exists. Without per-client limits and a bot check, spam can flood the lead list and exhaust the email quota | Absence in HTML: Observed. Server-side limits: Consideration | High | Rate limit by IP and email; add CAPTCHA or a honeypot field. Demo: `app/rate_limit.py` |
| S2 | **Payment confirmation integrity.** Registration is followed by a Cashfree payment, after which accounts are created and credentials emailed. If "paid" were decided from the browser redirect, it could be forged | Consideration (payment flow Observed) | High | Trust only the gateway's signed server-to-server webhook; verify the signature, process each event once, reconcile with the gateway. See `recommended-improvements.md` §4 |
| S3 | **Credential delivery by email.** The page says credentials are sent to the registration email. If that means a password in plain text, email is a weak channel | Observed text; mechanism **To verify** | High | Send a single-use, short-lived "set your password" link instead |
| S4 | **Several browser-protection headers are missing on `/contact`.** HSTS is present, but the response had no `content-security-policy`, `x-content-type-options`, `referrer-policy`, `x-frame-options` (or CSP `frame-ancestors`) or `permissions-policy` | **Observed** (headers read in DevTools, 31 Oct 2026) | Medium | Add them centrally in `next.config.js` or the host's header settings (see `recommended-improvements.md` §1). Build the CSP around the scripts actually used (Google Tag, payment widget) |
| S5 | **Third-party data processors.** Resend (email), Prisma (database layer), Cashfree (payments), Google Tag (analytics), Google Fonts and the hosting platform each touch visitor or personal data | Observed | Medium | Keep an inventory of processors, use least-privilege API keys stored as secrets, rotate periodically |
| S6 | **Framework disclosure.** The response includes `x-powered-by: Next.js`, which tells scanners which framework to target | **Observed** | Low | `poweredByHeader: false` in `next.config.js` |
 
## 2. Authentication & authorisation
 
| ID | Finding | Evidence | Priority | Recommendation |
|---|---|---|---|---|
| A1 | **Per-object authorisation.** The intern portal (own tasks, PR links, certificates) and Revio (Admin/Manager/Advisor, multiple locations) imply data that must be isolated per user or tenant. Hiding UI buttons is not access control | Consideration (portal and roles Observed) | High | Enforce checks on the server for every object read/write (`WHERE owner_id = :me`); add tests that user A cannot fetch user B's record (IDOR) |
| A2 | **Public certificate verification.** Certificates carry a public QR check. If identifiers are sequential, anyone can enumerate other people's certificates | Consideration (QR check Observed) | High | Use unguessable IDs (UUIDv4 or signed tokens), return minimal data, rate limit lookups |
| A3 | **Session and login hardening** for the portal: brute-force protection, secure/HttpOnly/SameSite cookies, short-lived tokens | To verify (portal is behind login, not inspected) | Medium | Lockout or progressive delay after failed attempts; cookie flags; refresh-token rotation |
 
## 3. Data validation & handling
 
| ID | Finding | Evidence | Priority | Recommendation |
|---|---|---|---|---|
| D1 | **Server-side validation on every form.** The contact form's fields (`fullName`, `email`, `company`, `industry`, `message`) carry only `required` and `type="email"`; there is no `maxlength`, `minlength` or `pattern`. Browser checks are bypassable, so length, format and unknown-field checks must exist on the server | Browser-side rules: **Observed**. Server-side rules: Consideration | High | Schema validation (zod in Next.js, Pydantic in FastAPI), with maximum lengths. Demo: `app/schemas.py` |
| D2 | **Duplicate submissions.** Double-clicks and retries can create duplicate leads or enrolments, and duplicate payment orders | Consideration | High | Idempotency keys + DB unique constraints. Demo: `app/idempotency.py` |
| D3 | **Privacy policy vs actual data flows.** The policy (updated 20 May 2026) names Resend and Prisma but not analytics. Google Tag loads on the contact page, and I found no consent-banner markup in the page HTML (a banner could be rendered later by JavaScript, so this is unconfirmed). The payment gateway and newsletter list are also not named | Google Tag and policy text: **Observed**. Consent banner: To verify | Medium | Align the policy with real processors; define retention periods; make deletion-on-request auditable. Review with qualified counsel (India's DPDP Act, 2023) |
 
## 4. Performance
 
| ID | Finding | Evidence | Priority | Recommendation |
|---|---|---|---|---|
| P1 | **Oversized image requests.** Student photos on `/bitelevate` are requested through the Next.js image optimiser at `w=3840`, far above what a small avatar needs | Observed in image URLs; delivered size **To verify** | Medium | Set accurate `sizes` on the image component so avatars request about 64-128 px variants (`recommended-improvements.md` §5) |
| P2 | **HTML caching is good; asset caching not yet checked.** The page is edge-cached (`x-vercel-cache: HIT`) and the browser revalidates it each visit (`cache-control: public, max-age=0, must-revalidate`, with an ETag giving a 304). That is a sensible pattern for HTML. The cache headers on `/_next/static/...` files were not checked | HTML: **Observed**. Static assets: To verify | Low | Confirm hashed assets are `immutable` with a long max-age |
| P3 | **Repeated blocks.** The testimonial section appears to render its cards twice (typical of a looping marquee), increasing DOM size and images loaded | Observed (duplicated content in the page text) | Low | Lazy-load off-screen images; consider a CSS-only loop that does not duplicate heavy content |
| P4 | **Database growth and query cost** as leads, enrolments, task submissions and reviews grow | Consideration | Medium | Index lookup columns (email, owner_id, status); paginate admin lists; cache hot reads in Redis |
| P5 | **Content starts invisible until JavaScript runs.** The server-rendered HTML sets `style="opacity:0"` on the page wrapper, the form and many sections. This is typical of scroll-reveal animations, but it delays when content appears and shows a blank page if scripts fail or load slowly | **Observed** (page HTML) | Medium | Render content visible by default and run the animation as an enhancement after hydration; respect `prefers-reduced-motion` |
| P6 | **Compute region may be far from the audience.** The `x-vercel-id` header reads `bom1::iad1::...`: an edge node in Mumbai plus `iad1`, which is Vercel's US East (Washington, D.C.) region. The audience is largely in India, so uncached dynamic work (form posts, database calls) may make a long round trip | Header: **Observed**. Meaning: Inferred | Low | Check the project's function region and place it, and the database, near India (for example `bom1`). See `recommended-improvements.md` §9 |
 
## 5. Error handling & reliability
 
| ID | Finding | Evidence | Priority | Recommendation |
|---|---|---|---|---|
| E1 | **Email delivery in the request path.** If the form handler waits for the email API, a provider slowdown makes the form slow or fail even though the data was saved | Consideration | Medium | Save first, queue the email, retry with back-off; surface failures in logs. Demo architecture in `audit-report.md` §6 |
| E2 | **Consistent, safe error responses.** Errors should share one JSON shape and never expose stack traces or SQL | Consideration | Medium | Central handlers. Demo: `app/errors.py`, `tests/test_health_and_errors.py` |
 
## 6. Architecture & observability
 
| ID | Finding | Evidence | Priority | Recommendation |
|---|---|---|---|---|
| R1 | **Uptime claim needs measurement.** The services page cites 99.9% uptime | Observed claim | Medium | Health checks, structured logs with request IDs, error tracking, alerts, a public status page |
| R2 | **Metadata consistency.** On `/contact`, `og:url` is the homepage (`https://cynbit.in`) while the structured data says `https://cynbit.in/contact`, and I found no `<link rel="canonical">` tag. Apex and `www` hosts are also mixed. Relevant since technical SEO is a listed service | **Observed** | Low | One canonical host with a 301 redirect; per-page canonical URL and `og:url` |
 
---
 
## Items for AI/LLM features (Consideration)
 
Cynbit Studio advertises AI code evaluation, mock interviews and AI-assisted review replies in
Revio. If these call third-party models or run user-submitted code on the server:
 
- sandbox any code execution (isolated container, no network, CPU/memory/time limits);
- apply per-user quotas and spend caps; use timeouts, retries and circuit breakers;
- treat model input as untrusted (prompt injection) and avoid sending unnecessary personal data;
- require human approval before AI replies are posted publicly.
 