# Recommended Improvements

**Deliverable 3 of 3** · Technical recommendations with architectural code snippets.

> **Status of the snippets.**
> - §2 (Python) and §3 (Python) are condensed from this repository's `app/` code, which is covered by 64 passing tests.
> - The TypeScript, Prisma and `next.config.js` snippets (§1, §2b, §3b, §5) are **illustrative patterns written for the stack the site appears to use** (Next.js + Prisma). I have *not* run them against Cynbit's code, and Cynbit may already do these things. Treat them as design sketches.

Findings referenced (S1, D1...) are defined in [`security-performance-findings.md`](security-performance-findings.md).

---

## 1. Security headers (S4)

If the checks in `api-observation-worksheet.md` show these headers are missing, a Next.js app
can add them centrally:

```js
// next.config.js  (illustrative; tune CSP to the site's real scripts before enabling it)
module.exports = {
  async headers() {
    return [{
      source: "/(.*)",
      headers: [
        { key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains" },
        { key: "X-Content-Type-Options",    value: "nosniff" },
        { key: "Referrer-Policy",           value: "strict-origin-when-cross-origin" },
        { key: "Permissions-Policy",        value: "camera=(), microphone=(), geolocation=()" },
        { key: "X-Frame-Options",           value: "DENY" },
      ],
    }];
  },
};
```

Why: HSTS forces HTTPS; `nosniff` stops browsers guessing file types; the others limit
data leakage and clickjacking. A Content-Security-Policy is valuable but must be built
carefully around the scripts actually in use (payment widget, analytics).

## 2. Server-side validation (D1)

### 2a. Python / Pydantic (this repo, `app/schemas.py`)

```python
class InquiryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    full_name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    company: str | None = Field(default=None, max_length=120)
    message: str = Field(min_length=10, max_length=2000)
```

### 2b. TypeScript / zod equivalent (illustrative)

```ts
import { z } from "zod";

export const InquirySchema = z.object({
  fullName: z.string().trim().min(2).max(100),
  email:    z.string().trim().toLowerCase().email(),
  company:  z.string().trim().max(120).optional(),
  message:  z.string().trim().min(10).max(2000),
}).strict();                       // .strict() rejects unknown fields

// in the route handler:
const parsed = InquirySchema.safeParse(await req.json());
if (!parsed.success) {
  return Response.json({ error: { code: "validation_error",
    details: parsed.error.issues.map(i => ({ field: i.path.join("."), message: i.message })) } },
    { status: 422 });
}
```

## 3. Duplicate-request prevention (D2)

### 3a. Python (this repo, `app/idempotency.py`)

```python
saved = _lookup(conn, key, endpoint, fp)      # seen this key before?
if saved is not None:
    response.headers["Idempotent-Replay"] = "true"
    return saved                              # replay, do NOT create again

with conn:                                    # one transaction:
    body = create(conn)                       #   1) create the record
    conn.execute("INSERT INTO idempotency_keys ...")   # 2) remember the answer
```

### 3b. Prisma model for the same idea (illustrative)

```prisma
model IdempotencyKey {
  key         String
  endpoint    String
  fingerprint String           // hash of the request body
  response    Json
  createdAt   DateTime @default(now())

  @@id([key, endpoint])        // the database guarantees only one winner in a race
}

model Enrollment {
  id        Int    @id @default(autoincrement())
  email     String
  domainLab String
  status    String @default("pending_payment")
  @@unique([email, domainLab]) // business rule enforced by the database
}
```

Create the enrolment and the key inside one `prisma.$transaction(...)`. If the unique
constraint fires for the key, read and return the stored response.

## 4. Payment webhook handling (S2)

The browser redirect after checkout is **not proof of payment**. The gateway's signed,
server-to-server webhook is. Follow the gateway's documentation for the exact signature
scheme; the shape of the handler is:

```python
def handle_webhook(raw_body: bytes, signature: str, event_id: str):
    expected = hmac.new(SECRET, raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):      # constant-time compare
        raise AppError(401, "bad_signature", "Invalid webhook signature.")

    if already_processed(event_id):                       # gateways can resend events
        return {"status": "duplicate_ignored"}

    mark_enrollment_paid(...)        # only now does status become 'paid'
    queue_welcome_email(...)         # one-time set-password link, not a plain password
```

Also reconcile periodically: list recent orders from the gateway's API and fix any the
webhook missed.

## 5. Right-sizing images (P1)

```tsx
// Illustrative: tell the optimiser the avatar is small so it does not request 3840 px.
<Image
  src={student.photo}
  alt={student.name}
  width={64}
  height={64}
  sizes="64px"          // browser asks for ~64-128 px variants, not 3840
  loading="lazy"
/>
```

Check the effect in DevTools -> Network -> Img -> Size before and after.

## 6. Shared rate limiting (S1)

The demo's limiter is in-memory (`app/rate_limit.py`, tested). With several servers use a
shared atomic counter:

```python
def allow(redis, client_id: str, limit: int = 5, window: int = 60) -> bool:
    key = f"rl:{client_id}:{int(time.time() // window)}"
    count = redis.incr(key)          # atomic across all servers
    if count == 1:
        redis.expire(key, window)    # counter cleans itself up
    return count <= limit
```

Add a bot check (CAPTCHA/honeypot) on top; rate limits alone do not stop slow, distributed spam.

## 7. Keep slow work out of the request (E1)

```python
# Request handler: save, enqueue, respond fast.
inquiry = save_inquiry(payload)
queue.enqueue(send_notification_email, inquiry.id)   # worker retries with back-off
return 201
```

A failed email then becomes a retry in a worker, not a failed form for the visitor.

## 8. Target architecture

See the diagram and component reasoning in [`audit-report.md`](audit-report.md) §6:
CDN/WAF -> front end -> API (validation, auth, rate limit) -> PostgreSQL + Redis ->
job queue/workers -> email/AI providers, with the payment webhook entering through the API
and everything reporting to logging and monitoring.

## Suggested order of work

| Order | Item | Why first |
|---|---|---|
| 1 | Verify headers and caching (worksheet) | Cheap, immediate evidence |
| 2 | Validation, rate limit, bot check on public forms (S1, D1) | Biggest abuse surface |
| 3 | Idempotency + unique constraints on registration (D2) | Prevents duplicate enrolments and orders |
| 4 | Payment webhook + one-time credential links (S2, S3) | Money and account security |
| 5 | Queue for email/AI work (E1) | Reliability |
| 6 | Image sizing, caching, indexes (P1, P2, P4) | Performance gains |
| 7 | Observability and status page (R1) | Makes uptime claims measurable |
