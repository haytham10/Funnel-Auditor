# Joel Arcus

<!-- airtable-record: TBD -->
> **Site:** https://stwtq.com/ · **Profile:** https://www.linkedin.com/in/joelarcus/
> **Walked:** 2026-07-19 · **Slug:** `joel-arcus`

---

## Overview

Joel Arcus runs "Stay With The Question" (stwtq.com), a solo life/leadership/mindset coaching practice based in Dubai, working worldwide. Custom Next.js site (not a hosted funnel builder). Main paid offer: a single 1:1 coaching session at a pre-launch $79 (reg. $540, code PRELAUNCH_SWTQ, offer ends Sep 30), booked via Calendly + Stripe in an embedded #coaching section on the homepage; also a free AI-coaching app (start free) and a book launching Sep 2026. 5,203 LinkedIn followers. "Powered by FalconBridge Partners" is corporate-advisory branding, not a gatekeeper on his solo coaching.

## Funnel Walk

- Stop 1 (Entry/home) — full custom sales page, hero "Stay with the question," clear #coaching offer section with Calendly+Stripe embedded checkout — real funnel, not a link hub.
- Stop 2 (Freebie) — /app/signup captures name+email for the free AI app before delivering — list-building present.
- Stop 3 (Offer/Sales) — homepage #coaching: single session $540 → $79, tabs Discovery / Coaching series / Corporate enquiry.
- Stop 4 (Checkout) — Calendly + Stripe embedded on the homepage offer section (no separate checkout URL to hop; JS-embedded, not click-resolvable via static fetch).
- Stop 5 (Audience ownership) — newsletter + freebie email capture on every page — owns a list.

## Evidence

- **Site vision pass:** `VISION PASS: COMPLETE — 7 of 7 required images confirmed read`
- **Pasted evidence:** none — crawl-only walk
- **Screenshots:** none promoted yet — see per-finding notes below

## Gates

- **Gate 0:** Pass — UAE base (homepage meta "Coach Joel — Dubai, working worldwide" + pre-flight li-profile Dubai); funnel confirmed ($79 Calendly/Stripe coaching offer live on home); activity (LinkedIn posted 5d ago); audience 5,203.
- **Gate 1:** Pass — own-face solo operator ("Coach Joel," first-person practice copy). FalconBridge Partners is "powered by" corporate-advisory branding, not a team gatekeeper on his solo coaching.
- **Lane:** Lane 1 (felt leak) — a broken conversion path on the money CTA.

## Findings — reasoning

**Rank 1 — pre-launch "Book a session" CTA is dead on /book and /blog**
Depth: DEEP (independently verified) — this is the site's primary money CTA, dead on two of the exact pages the homepage funnels readers to.
Type: dead anchor link (page-relative CTA broken off the homepage)
Innocent explanation: the "Book a session" button is a shared site-nav component using a relative #coaching fragment; it was built and tested on the homepage where the coaching section lives, so nobody noticed it points at a missing anchor once the same button renders on the book and blog pages.
Why it matters: the pre-launch "Book a session — $540 $79" button is dead on /book and /blog. The CTA uses a page-relative #coaching anchor that only exists on the homepage, so on the two subpages the persistent nav button (and the sticky floating one) scroll nowhere — the discounted offer is unreachable from the exact pages the site funnels readers to (the homepage hero's primary CTA sends people to /book). Independently verified: the /book and /blog CTA hrefs both resolve to `#coaching`, and a grep of both pages' HTML confirms zero `id="coaching"` present on either page; the homepage HTML has `<section id="coaching">` and its own CTA correctly uses the absolute `stwtq.com/#coaching`. The dead button was also confirmed rendered (not a mobile-only artifact) on desktop screenshots of both /book and /blog.
Loom skeleton (not sent, kept for a walkthrough offer): show /book (and /blog) with the "Book a session — $540 $79" button in the nav, click it on screen and show the page doesn't move, then show the working #coaching section on the homepage; fix would be pointing the "Book a session" nav/floating button to the absolute homepage anchor (stwtq.com/#coaching) instead of a page-relative #coaching, so it works from every page; done state is clicking "Book a session" from the book or blog page landing the visitor on the live $79 booking section every time.
Evidence: none promoted yet (raw archive cites evidence/joel-arcus/screenshots/stwtq_com_book_desktop.png, stwtq_com_blog_desktop.png, and evidence/joel-arcus/_firecrawl_raw/1.html, 2.html, 4.html).

**Rank 2 — free-app signup stacks five mandatory consent checkboxes** *(RESERVED — not yet sent)*
Depth: SHALLOW — top-of-funnel friction, not a broken path.
Type: signup friction (consent checkbox stack)
Innocent explanation: legal/consent requirements for an AI coaching tool that were added for compliance without a second pass on signup drop-off.
Why it matters: the free-app signup ("Bring your question. Start free.") stacks five separate mandatory consent checkboxes (18+, coaching-not-therapy, AI-processing, crisis, terms) before a free account can be created — heavy friction on the top-of-funnel free entry point, where friction costs the most volume.
Evidence: none promoted yet.

Two machine flags were rejected on the vision pass and not banked: "blog-stale" (miscomputed "126 days"; the newest post is 28 May 2026, ~52 days, and the activity floor already passed on LinkedIn 5 days ago) and "bio-ambiguity" (the home page is a full sales page, not a link hub).

## SMYKM Hook

`His July 17 post — "Agreement is easy. Action is not." — on how a real question keeps following you (it shows up in the shower, in the car, at 2am), which is exactly why he built his Stay With The Question sessions the way he did.` — **WORK** — source: https://www.linkedin.com/posts/joelarcus_staywiththequestion-joelarcus-thethreshold-activity-7483702020844023808-Sd75

---

*Email history lives in Airtable (`Touches` table) — every send and reply, verbatim.
Price discovery answer and anchor live on the Airtable `Leads` record.
Neither is duplicated here.*
