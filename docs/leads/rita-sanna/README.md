# Rita Sanna

<!-- airtable-record: TBD -->
> **Site:** https://ritasanna.com/rita-sanna-the-growth-lab/ · **Profile:** https://ae.linkedin.com/in/ritasanna
> **Walked:** 2026-07-20 · **Slug:** `rita-sanna`

---

## Overview

Rita Sanna — solo leadership/individual coach and consultant, Dubai (Founder, Rita Sanna Coaching & Consulting, Jul 2023–present). WordPress site (Elementor). Main offer walked: "The Growth Lab," a 3-week live cohort experience (USD 990) sold via a Stripe checkout, plus a free discovery call booked through HubSpot. LinkedIn is her main channel (11,447 followers, actor-confirmed).

## Funnel Walk

- Stop 1 (Entry — sales page ritasanna.com/rita-sanna-the-growth-lab/) — clean single CTA ("RESERVE YOUR SEAT"), price USD 990 shown clearly within 10 seconds.
- Stop 3 (Offer/Sales) — the cohort's own dates are stale: 3 live sessions dated Jan 12/19/26, 2026, and a private coaching window "between 1st December 2025 and 30th January 2026" — all 175-235 days in the past against the 2026-07-24 verification date — while the page still reads "Limited Seats ~ Starts 12-01-2026" as if upcoming.
- Stop 4 (Checkout) — the "RESERVE YOUR SEAT" button (via bit.ly/3JmBPf5) resolves to a LIVE, fully working Stripe checkout (book.stripe.com/eVq7sM6MNc481GO2NN4F200) still charging $990.00 for "The Growth Lab" — i.e. the page is actively able to take payment for a cohort whose live sessions already happened.
- Stop 4 (Booking, separate free-call CTA on the homepage) — the HubSpot scheduler ("Meet with Rita Sanna") shows zero available times at either duration (25/45 min) for the current month, with a banner "There are no available times with this duration with Rita Sanna today" / "No available dates in July," falling back to "email them at rita@ritasanna.com."
- Stop 5 (Audience ownership) — no freebie, opt-in, or email-capture form found anywhere in the crawled funnel (sales page or homepage) — only a generic "contact me" form. Her only reachable channel is LinkedIn (11,447 followers), fully rented.

## Evidence

- **Site vision pass:** `VISION PASS: COMPLETE — 6 of 6 required images confirmed read`
- **Pasted evidence:** none — crawl-only walk (Firecrawl-primary; Stripe checkout + HubSpot booking + bit.ly interstitial fetched as external stops).
- **Independent verification:** VERIFIED — stale Growth Lab cohort dates (Jan 12/19/26 2026 sessions; private window ended Jan 30 2026) confirmed live in the evidence package's raw HTML and the desktop screenshot; the RESERVE YOUR SEAT href confirmed as bit.ly/3JmBPf5 in the same HTML and a screenshot; a live re-fetch on 2026-07-24 confirms bit.ly/3JmBPf5 still 301-redirects to book.stripe.com/eVq7sM6MNc481GO2NN4F200, which returns HTTP 200 with an active $990.00 card-entry "Book" form for "The Growth Lab" / RITA SANNA - FZCO — no expired/disabled messaging present.
- **Screenshots:** none promoted yet — see per-finding notes below. One machine flag was rejected in the vision pass — a Tier A "price_mismatch" between USD990 (sales page) and $990.00 (Stripe checkout) was rejected as same-number-different-currency-symbol, not an actual mismatch (confirmed identical price on both screenshots).

## Gates

- **Gate 0:** Pass — UAE-based (Dubai, LinkedIn profile confirmed), funnel exists (live $990 Stripe checkout confirmed reachable and functional), activity (LinkedIn posts within 24h per qualifying pass), audience (11,447 LinkedIn followers, actor-confirmed).
- **Gate 1:** Pass — solo practice (Founder since Jul 2023), no team/agency footer, no gatekeeper; her Associate roles elsewhere are external affiliations, not staff on this offer.
- **Lane:** Lane 1 (felt leak) on a real, currently-buyable funnel.

## Findings — reasoning

> The **canonical, structured** copy of each finding lives in Airtable (`Findings` table):
> rank, status, depth, type, innocent explanation, evidence path. This section carries the
> *reasoning* — why it's deep vs shallow, why it stings, what was ruled out. Don't duplicate
> the fields here; they will drift.

**Rank 1 — a live checkout still takes payment for a cohort that already happened**
Depth: SHALLOW (per raw archive bank tag: `UNUSED | SHALLOW`) · Type: stale offer still live behind a working checkout
Innocent explanation: the page likely wasn't updated after the last cohort closed — an easy miss on a static Elementor page that isn't tied to a live calendar feed.
Why it matters: the "Growth Lab" cohort's own sessions (Jan 12/19/26, 2026) and private-coaching window (ended Jan 30, 2026) are already 6+ months past, yet "RESERVE YOUR SEAT" still routes to a live, working $990 Stripe checkout that would take a stranger's payment right now for dates already gone.
Evidence: none promoted yet

**Rank 2 — the free discovery-call scheduler shows zero availability all month** *(RESERVED — call bait, never emailed)*
Depth: SHALLOW (per raw archive bank tag: `UNUSED | SHALLOW`) · Type: dead lowest-friction entry point
Innocent explanation: the connected calendar may just need a re-sync or the month's slots haven't been opened yet.
Why it matters: the free discovery-call scheduler (HubSpot, linked from the homepage) shows zero available times at any duration for the entire current month, dead-ending the lowest-friction path to reach her.
Evidence: none promoted yet

**Rank 3 — no owned email list anywhere in the funnel** *(RESERVED — call bait, never emailed)*
Depth: DEEP (per raw archive bank tag: `RESERVED | DEEP`) · Type: missing owned-audience mechanism
Innocent explanation: growth has likely come from referrals/1:1 outreach, so building an owned list may simply not have felt urgent yet.
Why it matters: no email capture or freebie anywhere in the funnel (sales page or homepage) — the entire reachable audience is rented on LinkedIn (11,447 followers) with no owned list, so a platform change or algorithm shift has no backup.
Evidence: none promoted yet

The Loom skeleton drafted for Rank 1 shows ritasanna.com/rita-sanna-the-growth-lab/ — the "RESERVE YOUR SEAT" button and the Stripe checkout it opens (book.stripe.com/eVq7sM6MNc481GO2NN4F200), side by side with the stale "DATE ~ 12th January 2026" session copy. Fix: update the cohort dates/copy for the next live round (or pull the page until the next round is scheduled) so the checkout can't take payment against dead dates. Done state: the page shows an upcoming cohort date, and "RESERVE YOUR SEAT" opens a checkout that matches it.

## SMYKM Hook

`her LinkedIn post from ~6 hours ago reframing "Why aren't they...?" into "What has this system taught them to do?" — a leadership team called their people "risk-averse" until she observed their meetings and found every mistake scrutinized and every challenge instantly answered by the leader, so silence was a survival strategy, not a personality trait` — **WORK** — source: https://www.linkedin.com/posts/ritasanna_%F0%9D%97%9F%F0%9D%97%B2%F0%9D%97%AE%F0%9D%97%B1%F0%9D%97%B2%F0%9D%97%BF%F0%9D%98%80%F0%9D%97%B5%F0%9D%97%B6%F0%9D%97%BD-%F0%9D%97%AF%F0%9D%97%B2%F0%9D%97%B0%F0%9D%97%BC%F0%9D%97%BA%F0%9D%97%B2%F0%9D%98%80-%F0%9D%97%B2%F0%9D%97%AE%F0%9D%98%80%F0%9D%97%B6%F0%9D%97%B2%F0%9D%97%BF-activity-7486308238221631490-Vv_u

---

*Email history lives in Airtable (`Touches` table) — every send and reply, verbatim.
Price discovery answer and anchor live on the Airtable `Leads` record.
Neither is duplicated here.*
