# Website Observations - Cynbit Technologies (cynbit.in)
 
**Observed on:** 31 October 2026
**Method:** Reading the publicly visible text of public pages only. No requests were
sent to any API, no forms were submitted, nothing was scanned or load-tested.
**Purpose:** This file is the *evidence log*. The analysis built on it is in
[`audit-report.md`](audit-report.md).
 
> Public pages change. Everything below describes what the pages said on the date above.
 
Each item is tagged:
 
- **[Seen]** - stated on a public page
- **[Inferred]** - a reasonable conclusion from what was seen; *not confirmed*
- **[To verify]** - cannot be known from page text; see the checklist at the end
---
 
## 1. What the company is
 
| Item | Observation | Tag |
|---|---|---|
| Name / location | Cynbit Technologies, Pratap Nagar, Jaipur, Rajasthan 302033 | [Seen] |
| What it sells | AI automation (agents, LLM automation, voice agents), custom software and cloud, digital marketing / technical SEO | [Seen] |
| Products | Cynbit Studio (career-growth / learning platform), TenantEase (property and tenant management), Revio (AI review and reputation management) | [Seen] |
| Training programme | BitElevate: 60-day remote internship programme, six "labs" (Full Stack, Python Backend, AI, Frontend, QA, UI/UX), enrolment fee shown on page | [Seen] |
| Careers | 20 live openings (12 internships, 8 full-time), including a *Backend Developer Intern* (Remote / Jaipur) | [Seen] |
 
## 2. Site map (from the navigation)
 
`/` · `/story` · `/team` · `/careers` (+ one detail page per role) · `/impact` · `/services` ·
`/products` · `/case-studies` · `/bitelevate` · `/bitelevate/paths` · `/diaries` · `/blog` ·
`/contact` · `/privacy` · `/terms` · `/cookies` · `/navigation`  **[Seen]**
 
## 3. Forms and data-collection points
 
| # | Where | Fields visible | Notes | Tag |
|---|---|---|---|---|
| F1 | `/contact` - "The Blueprint" | Full Name, Email Address, Company *(optional)*, Industry *(optional)*, Your Message; button **Send Inquiry** | Page promises a response within 24 hours | [Seen] |
| F2 | `/products` - "Schedule a Demo" | Product choice (Studio / TenantEase / Revio), Full Name, Work Email, Company Name, "How can we help?" | One form shared by three products | [Seen] |
| F3 | `/bitelevate` - "Direct Sprint Registration" | Full Name, University/College, Email *("credentials sent here")*, Phone/WhatsApp, Preferred Domain Lab (6 options), Sprint Duration, Referral Code *(optional)*, career goals | Followed by a payment step through **Cashfree** (UPI, cards, net banking). Page text says the intern-portal account is created automatically and credentials are emailed after payment settles | [Seen] |
| F4 | Footer on every page - "Subscribe to our Briefing" | A "Join the Newsletter" element is shown; no email input for it appears in the `/contact` page HTML | Page states a large subscriber count (a marketing claim, not verified). How sign-up works is unconfirmed | [Seen] / [To verify] |
| F5 | `/careers/<role>` | Per-role pages exist | Application mechanism not visible in the page text read; the generic "drop a portfolio" link points to `/contact` | [Seen] / [To verify] |
| F6 | Private "Intern Portal" | Daily tasks, pull-request link submission, mentor review, exam-leave freeze request, certificate with public QR verification | Behind login, so not inspected | [Seen] (described only) |
 
## 4. Technology signals
 
| Signal | Evidence | Tag |
|---|---|---|
| Front end is Next.js | Image URLs use the `/_next/image?url=...&w=...&q=75` pattern, pages carry a `next-size-adjust` meta tag, and the `/contact` response sends `x-powered-by: Next.js` | [Seen] |
| Prisma used for the database layer | Stated in the privacy policy | [Seen] |
| Resend used for email delivery | Stated in the privacy policy | [Seen] |
| Cashfree used for payments | Named on the BitElevate registration section | [Seen] |
| Offered tech stack | Services page lists FastAPI, Django, NestJS, Next.js, PostgreSQL, MongoDB, Redis, Supabase, AWS, Azure, Docker, Kubernetes... | [Seen] - this is what the company *offers*, **not** proof of what powers this website |
| Python Backend Lab curriculum | Names JWT, RBAC, Redis caching, Celery/async queues, Docker, GitHub Actions, `pytest --cov=app` | [Seen] |
| Backend/database brand claims | Services page claims "optimized for 99.9% uptime" and "zero-trust security" | [Seen] - marketing claims, not verified |
 
## 5. Privacy policy (last updated 20 May 2026, per the page)
 
- Says only the minimum is collected: "typically name, email and professional context" via forms **[Seen]**
- Says data is not sold or rented for marketing **[Seen]**
- Names Resend (email) and Prisma (database) as partners **[Seen]**
- Offers copy/deletion of personal data by emailing the contact address **[Seen]**
- Does **not** mention the payment gateway, the newsletter list, phone numbers, or analytics tools by name **[Seen]** (the policy may be intentionally short; worth aligning with actual data flows)
## 6. Page-metadata observations
 
| Observation | Tag |
|---|---|
| Several pages (`/contact`, `/services`, `/products`, `/careers`, `/privacy`) declare `og:url` as the bare homepage `https://cynbit.in` rather than their own address. `/bitelevate` is different: it declares its own canonical URL and `og:url` | [Seen] |
| Internal links use the `www.cynbit.in` host while metadata uses the bare `cynbit.in` host | [Seen] |
| Student photos on `/bitelevate` are requested through the image optimiser at `w=3840` (a very large width) | [Seen] in link URLs; the actual bytes delivered are [To verify] |
 
---
 
## 6b. Passive browser checks (Chrome DevTools, `/contact`, 31 Oct 2026)
 
| Observation | Tag |
|---|---|
| Framework is Next.js (App Router chunks; `x-powered-by: Next.js`) | [Seen] |
| Hosted on Vercel (`server: Vercel`; `x-vercel-cache: HIT`; `x-vercel-id: bom1::iad1::...`) | [Seen] |
| `strict-transport-security: max-age=63072000`; `content-encoding: br`; `etag` present; `cache-control: public, max-age=0, must-revalidate`; document returned 304 on revalidation | [Seen] |
| No `content-security-policy`, `x-content-type-options`, `referrer-policy`, `x-frame-options` or `permissions-policy` in the response | [Seen] |
| Contact form fields: `fullName`, `email`, `company`, `industry`, `message`; only `required` and `type="email"`; no `maxlength`/`minlength`/`pattern`; no `action` attribute; no CAPTCHA, honeypot or CSRF token in the HTML | [Seen] |
| Page HTML starts content at `style="opacity:0"` (revealed by script) | [Seen] |
| `og:url` is the homepage; no `<link rel="canonical">`; JSON-LD uses `/contact` | [Seen] |
| Google Tag (analytics) and Google Fonts are the only third-party resources in the HTML | [Seen] |
| 41 requests, about 1.7 MB transferred on one load | [Seen] (varies with caching) |
| Which endpoint the form calls, and the JSON it sends | [To verify] (read the contact page's own JS chunk) |
| Cache headers on `/_next/static/...` assets; Lighthouse scores | [To verify] |
 
## 7. What is NOT known from page text - verify yourself (about 10 minutes)
 
Open the site in your own browser, press **F12 -> Network tab**, and just *browse* (do not
submit forms with junk data on a production system). Then fill in:
 
| Question | How to check | What you found |
|---|---|---|
| Is HTTPS enforced and does `http://` redirect? | Type `http://cynbit.in` in the address bar | |
| Does `cynbit.in` redirect to `www.cynbit.in` (or the reverse)? | Watch the URL after loading | |
| Which security headers come back? (`Strict-Transport-Security`, `Content-Security-Policy`, `X-Content-Type-Options`, `Referrer-Policy`) | Network -> click the first document request -> Headers | |
| Are static assets cached? (`Cache-Control` on `/_next/static/...`, images) | Network -> click an asset -> Headers | |
| How large is the page / how many requests? | Bottom bar of the Network tab | |
| What size are the testimonial images actually delivered at? | Network -> filter "Img" -> check Size column | |
| Is there a public `/api/...` route used by the forms? | Network -> filter "Fetch/XHR" while browsing | |
| Are Lighthouse scores acceptable? | DevTools -> Lighthouse -> Analyze page load | |
 
Anything you cannot confirm should stay labelled **[To verify]** in your report; being
precise about that is a strength, not a weakness.
 
## Sources (all public pages, read 31 Oct 2026)
 
- https://www.cynbit.in/contact
- https://www.cynbit.in/services
- https://www.cynbit.in/products
- https://www.cynbit.in/bitelevate
- https://www.cynbit.in/careers
- https://www.cynbit.in/privacy
- https://github.com/Cynbit-Technologies/.github (organisation profile)