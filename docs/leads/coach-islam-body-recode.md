# Coach Islam (Body Recode)

<!-- airtable-record: TBD -->
> **Site:** https://bodyrecodeae.com/ · **Profile:** https://ae.linkedin.com/in/islam-mohamed-fahmy
> **Walked:** 2026-07-15 · **Slug:** `coach-islam-body-recode`

---

## Overview

Coach Islam, solo founder of Body Recode (Body Recode Lifestyle Coaching FZE LLC), a certified personal trainer and online fitness coach based in Dubai, UAE. Custom-built single-page site (React/Next.js, "direct"/custom platform, not a template builder). Offer ladder: 1-month 1-on-1 PT (1,999 AED), 3-month transformation (5,550 AED, "Most Popular"), and a low-ticket "Body Recode Online Coaching App" (100 to 50 AED/mo, "50% OFF, Limited Time"). Claims 10+ years, 500+ transformations. ~19,080 IG audience.

## Funnel Walk

- Stop 1 (Landing/hero) — "Recode Your Body / Upgrade Your Lifestyle" with "Book a Free Call" + "View Programs" — entry loads clean; everything routes to a consultation.
- Stop 3 (Offer/pricing) — three-tier ladder with visible AED prices, strong social proof (before/after cards, testimonials, "vs generic coaching" table, FAQ) — complete, professional sales page.
- Stop 4 (Checkout) — NOT REACHED. No checkout/payment/app-store link anywhere on the site; all three product CTAs ("Book Now", "Start Today", "Subscribe for 50 AED") are hrefless JS buttons. `cta-probe` returned no_visible_change for all — but also for the language toggle (which should change the page), so its change-detection is unreliable here and button behavior can't be visually confirmed. High-ticket PT routing to a consultation form is by design; the 50 AED app's missing self-serve checkout is a candidate leak but unconfirmable from this crawl.
- Stop 5 (Audience ownership) — consultation form captures email — owns a list-building mechanism.

## Evidence

- **Site vision pass:** `VISION PASS: COMPLETE — 2 of 2 required images confirmed read`
- **Pasted evidence:** none — crawl-only walk.
- **Screenshots:** none promoted yet — see per-finding notes below

## Gates

- **Gate 0:** Pass — UAE base confirmed (Dubai; Body Recode Lifestyle Coaching FZE LLC; +971 56 867 4665; "Dubai, United Arab Emirates" on contact). Funnel present (sales page, AED prices). Audience 19,080, well over the 1,500 floor. Activity: live, maintained modern site + regular IG cadence (from qualifying) + active UAE LinkedIn.
- **Gate 1:** Pass — solo founder Coach Islam; single-operator voice throughout; no team/agency/gatekeeper.
- **Lane:** Lane 2 (no leak) — complete, recently-built, professionally-executed funnel; no visually-confirmable broken or stale element.

## Findings — reasoning

No Lane 1 finding was banked for this lead — the Findings Bank is empty. The one candidate leak (the 50 AED app's missing self-serve checkout) could not be visually confirmed and is not banked.

Ruled out in the vision pass: one machine flag was rejected — `cta-probe`'s "no_visible_change" on the 50 AED app / PT buttons was rejected as a dead-button finding, because the probe also reported no change on the language toggle (which should visibly change the page), making its change-detection unreliable here and not visually confirmable from a static screenshot.

**Warm-up angle (not a Lane 1 finding, not for cold send)**
The only real opportunity is the missing self-serve / lead-capture middle — a 19K IG audience is driven to a site whose sole ask is "book a free consultation," while the 50 AED app is the one self-serve product yet has no visible checkout to actually buy it. That is an "add something" conversation, not a "something is broken" opener — so it holds as warm-up, not a cold send.

## SMYKM Hook

`not run yet — see haytham-hook-finder`

---

*Email history lives in Airtable (`Touches` table) — every send and reply, verbatim.
Price discovery answer and anchor live on the Airtable `Leads` record.
Neither is duplicated here.*
