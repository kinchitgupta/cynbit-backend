# API Observation Worksheet (passive checks)

The brief asks for **observable API structure and payloads**. That can only be seen from a
browser, so this worksheet is for **you** to fill in with what you actually see. Results here
feed the audit report. Do not copy anything you did not observe.

## Rules (from the brief)

Only **passive and authorized** testing is permitted. So:

- **Do:** browse pages normally, read what the browser loads, read public JavaScript files, read response headers.
- **Do not:** submit forms with fake or test data, replay or edit requests, fuzz, scan, brute-force, send many requests, try other users' IDs, or open anything behind a login you don't own.
- **If you want to submit one real test inquiry**, ask the Cynbit contact (Aria, Talent Acquisition) for written permission first. Until then, treat form submission as out of bounds.

## Step A: Page-load observations (about 10 minutes)

1. Open Chrome, press **F12**, go to the **Network** tab, tick **Disable cache**, and load `https://cynbit.in/contact`.
2. Click the very first request (the document) -> **Headers** -> **Response Headers**. Record the table below.
3. Filter by **Fetch/XHR**. Note any requests that appear on page load (there may be none).
4. Filter by **Img**; check the **Size** column on the student photos (relates to finding P1).
5. Look at the bottom bar: number of requests, total transferred, load time.
6. Run **Lighthouse** (DevTools -> Lighthouse -> Analyze page load) and note Performance, Accessibility, Best Practices, SEO scores.

### Response headers (fill in: present / absent, and value)

| Header | Present? | Value |
|---|---|---|
| `Strict-Transport-Security` | | |
| `Content-Security-Policy` | | |
| `X-Content-Type-Options` | | |
| `Referrer-Policy` | | |
| `X-Frame-Options` or CSP `frame-ancestors` | | |
| `Permissions-Policy` | | |
| `Cache-Control` (document) | | |
| `Cache-Control` (`/_next/static/...` file) | | |
| `Server` / `X-Powered-By` (does it reveal technology?) | | |
| Does `http://cynbit.in` redirect to HTTPS? | | |
| Does apex redirect to `www` (or reverse)? | | |

## Step B: Find the form's API call by reading public code (passive)

You can learn the API shape **without submitting anything** by reading the site's own public JavaScript.

1. Network tab -> filter **JS** -> reload `/contact`.
2. Open **Sources** (or click a JS file in Network -> **Response**). Use **Ctrl+Shift+F** (search across all files) and search for: `fetch(`, `/api/`, `"Send Inquiry"`, `JSON.stringify`.
3. Record what the client code reveals.

| Question | What the code shows |
|---|---|
| Does the form call an endpoint (`/api/...`) or a framework server action? | |
| HTTP method | |
| JSON field names sent (e.g. `name`, `email`...) | |
| Any client-side validation rules (min lengths, patterns)? | |
| Is a CAPTCHA/bot-check script loaded? | |
| Is any API key or secret visible in client code? (If you see one, **do not use it**; just note that one exists) | |
| Analytics / third-party scripts loaded | |

Repeat for the `/bitelevate` registration section (Cashfree script? redirect or popup checkout?) and the footer newsletter form.

## Step C: Summarise API structure (fill in only what you saw)

| Endpoint / mechanism | Method | Request fields | Response / behaviour | Source of evidence |
|---|---|---|---|---|
| | | | | |
| | | | | |

## Step D: Turn results into report text

For each row you filled in, add or update a finding in
`security-performance-findings.md`:

- Header present -> note it as a **strength**.
- Header absent -> change that finding from **To verify** to **Observed**, and keep the recommendation.
- Anything you could not check -> leave as **To verify**. Honest gaps are fine.

## Evidence log (your notes, with date/time)

```
Date/time checked:
Browser/version:
Notes:
```
