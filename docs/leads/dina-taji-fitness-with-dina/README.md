# Dina Taji (Fitness with Dina)

<!-- airtable-record: TBD -->
> **Site:** https://www.fitnesswithdina.com/ · **Profile:** https://www.instagram.com/fitnesswithdina/
> **Walked:** 2026-07-24 · **Slug:** `dina-taji-fitness-with-dina`

---

## Overview

Dina Taji, Fitness with Dina — solo fitness/health coach based in Dubai, UAE (self-tagged, and her own copy: "we built a cat sanctuary here in the UAE"). WordPress/Elementor site funnels through an internal Sign Up page into an external Trainerize-hosted subscription checkout. Main offer: a personal coaching app with home-workout programs, meal plans, and holistic coaching, sold on a monthly subscription. Audience: 114K on Instagram (@fitnesswithdina, public bio count, "Dubai" self-tagged; also TikTok 70.7K). 20+ years coaching experience; runs a linked cat-rescue nonprofit (Dubai Street Kitties) woven into the brand story.

## Funnel Walk

- Stop 1 (Bio/homepage) — clean single CTA ("Sign up now") into three paid tiers displayed as if live today ($30 Essential / $300 Connected / 1500 AED VIP monthly) — but the header nav simultaneously carries a "NEW APP LAUNCHING SOON" badge, an early signal of the mismatch confirmed further down the funnel.
- Stop 2 (Freebie) — none found; not a freebie-led funnel, straight to paid signup (vitamin, not flagged).
- Stop 3 (Offer/Sales — sign-up page) — opens with copy about a "fresh new app next year" (waitlist framing), then immediately below shows a live BASIC PLAN ($29.99/mo, purchasable) and a PREMIUM PLAN ($79.99/mo, displayed with the price crossed out and labeled "Not available") — a paid tier is shown to every visitor as currently unbuyable. These prices also don't match the homepage's $30/$300/1500 AED tier structure — three different price architectures across three pages of the same offer.
- Stop 4 (Checkout) — the "join us now" button leaves the site entirely for a Trainerize-hosted checkout (trainerize.me/checkout/beyondfitness8/...). That checkout page reads "Unable to accept live payments. Join the waiting list to be notified once we are ready to take new clients." — confirmed on both desktop and mobile renders. The entire paid path currently cannot take a payment.
- Stop 5 (Audience ownership) — an email-capture form exists (contact page, sign-up page), so not fully rented — not flagged.

## Evidence

- **Site vision pass:** `VISION PASS: COMPLETE — 6 of 6 required images confirmed read`
- **Pasted evidence:** none — crawl-only walk.
- **Screenshots:** none promoted yet — see per-finding notes below

## Gates

- **Gate 0:** Pass — UAE base confirmed (own copy: cat sanctuary "here in the UAE"; IG self-tagged Dubai; LinkedIn ae.linkedin.com/in/dina-taji). Funnel confirmed real (three paid subscription tiers, live sign-up + checkout flow, though checkout is currently non-functional — that's the finding, not a floor fail). Activity floor holds per intake notes (IG posts July 3 & 7 2026). Audience floor clears on a hard number (114K IG).
- **Gate 1:** Pass — single-person brand throughout ("I", "me"), no team/agency language, LinkedIn lists her as CEO/founder, personal story-driven About page.
- **Lane:** Lane 1 (felt leak) — a real committed buyer (three-tier paid app, 20 years in business, 114K real audience) with a provable, visually-confirmed leak at the buy moment.

## Findings — reasoning

**Rank 1 — Checkout itself cannot accept a payment**
Depth: DEEP · Type: broken checkout (RESERVED — call bait, not the opener finding used)
Innocent explanation: likely mid-transition to the new app (nav says "launching soon," the sign-up page pitches a waitlist for "a fresh new app next year") and the old payment processor got disconnected or paused during that transition without anyone routing the live "Sign Up"/"join us now" buttons away from it.
Why it matters: the actual checkout ("join us now" → Trainerize) currently reads "Unable to accept live payments — join the waiting list," so nobody clicking through the Sign Up page can complete a purchase right now, confirmed on desktop and mobile.
Evidence: none promoted yet

**Rank 2 — Three different price architectures across three pages of the same offer** *(UNUSED)*
Depth: DEEP · Type: pricing mismatch across funnel
Innocent explanation: the Sign Up + checkout pages are likely the older Trainerize-era pricing structure, and the homepage was updated to a newer tier structure without the downstream pages being brought in line.
Why it matters: pricing is architected three different ways across the funnel — the homepage lists $30 Essential / $300 Connected / 1500 AED VIP monthly tiers, the Sign Up page lists $29.99 Basic / $79.99 Premium, and the checkout itself charges $29.99 — a visitor comparing the homepage promise to what Sign Up/checkout actually offer hits a seam that doesn't reconcile.
Evidence: none promoted yet

**Rank 3 — Premium plan shown live but marked "Not available"** *(UNUSED — this is the opener finding used)*
Depth: SHALLOW · Type: unbuyable price displayed
Innocent explanation: the tier is probably paused for the same app-transition reason and the display was never hidden or removed from the live page.
Why it matters: the Sign Up page shows a PREMIUM PLAN at $79.99/month with the price crossed out and labeled "Not available," displayed live next to the purchasable Basic Plan — the opening angle used for outreach: a paid tier shown to every visitor comparing options as something they can't actually buy.
Loom / fix path: show the Sign Up page (fitnesswithdina.com/sign-up/) — the PREMIUM PLAN card showing "$79.99, Not available" next to the live Basic Plan. Fix: either hide/remove the Premium Plan card until it's actually sellable again, or reactivate it — a live page should never display a price it can't sell. Done state: a visitor sees only tiers that are actually purchasable — no crossed-out price sitting next to a "Buy" button.
Independent verification: VERIFIED — PREMIUM PLAN at $79.99/month, price crossed out and labeled "Not available," confirmed on the Sign Up page screenshot.
Evidence: none promoted yet

Ruled out in the vision pass: no machine flags were rejected — the single machine-flagged reconciliation entry (a price_mismatch between the sign-up page and checkout) was visually confirmed, not rejected; the homepage-vs-sign-up-page mismatch (rank 2 above) was found during vision reading, not flagged by machine checks.

## SMYKM Hook

`Her Instagram post from July 7, 2026 announcing the new app went live on Google Play for Android (soft launch, iOS still pending Apple review)` — **WORK** — source: https://www.instagram.com/p/DafdNWbOCZH/

---

*Email history lives in Airtable (`Touches` table) — every send and reply, verbatim.
Price discovery answer and anchor live on the Airtable `Leads` record.
Neither is duplicated here.*
