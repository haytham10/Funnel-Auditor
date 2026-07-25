# Donna Brown

<!-- airtable-record: TBD -->
> **Site:** https://dbdonnabrown.com/ · **Profile:** https://www.linkedin.com/in/donna-brown-35795a21
> **Walked:** 2026-07-15 · **Slug:** `donna-brown`

---

## Overview

Donna Brown is an ICF-certified life & leadership coach based in Dubai (DIFC), with an HR / Learning &
Development background (intake notes a FT Emirates NBD HR role). Solo operator on a custom-built site
(dbdonnabrown.com, hand-coded, Kit newsletter, Stripe payment links). Offers 1:1 coaching, group
coaching, a manual discovery-call request, and a self-serve course line delivered as PDF: Your Core
Blueprint (AED 597), three AED 797 courses, and the Complete Growth Bundle (AED 1,997). Audience not
independently confirmed (namesake collisions — many Donna Browns).

## Funnel Walk

- Stop 1 (Home) — clean hero, offerings, featured courses, testimonials, Kit opt-in — coherent, no leak.
- Stop 2 (Booking /book-a-call) — custom request form (not a live calendar); "Donna will confirm your
  preferred time personally by email within 24 hours." Manual but functional. Success/error banners in
  the HTML are correctly hidden by CSS (not shown by default).
- Stop 3 (Course directory) — lists 4 courses + bundle; bundle shows "AED 2,797" struck through then
  "AED 1,997" with a "Save 35%" badge.
- Stop 4 (Sales pages: Your Core Blueprint, Complete Growth Bundle) — full sales copy, Stripe "Enroll
  Now" CTAs; no price shown on the individual sales pages (price only appears in the directory + at
  checkout).
- Stop 5 (Checkout — Stripe payment links) — Core Blueprint AED 597.00 and Bundle AED 1,997.00, both
  match the site. The Core Blueprint checkout carries an "Add to your order" bump: "The Complete Growth
  Bundle AED 1,997.00 — Add" — but the bundle already includes Your Core Blueprint. Both checkouts are
  branded "Coaching Business" / "Pay Coaching Business", not Donna Brown.

## Evidence

- **Site vision pass:** `VISION PASS: COMPLETE — 12 of 12 required images confirmed read`
- **Pasted evidence:** none — crawl-only walk (Notion page body was blank). Machine flags rejected in
  the vision pass: 3 — booking success-banner (hidden by CSS), Core-Blueprint "Personal Invitation"
  YouTube embed = wrong video "Nano Banana Pro" (section is display:none, not visible to a visitor),
  site-vs-Stripe price mismatch (checked — prices match).
- **Screenshots:** none promoted yet — see per-finding notes below

## Gates

- **Gate 0:** Pass — UAE base confirmed (Dubai/DIFC, site + booking page + LinkedIn "Dubai, UAE"); funnel
  floor clear (live Stripe checkout AED 597–1,997 + booking). Activity (site freshly built, 2026, live
  checkout + active Kit newsletter) and audience 1,500+ are intake-trusted, NOT independently confirmed
  this run (namesake collisions obscure her own channels; Apify unavailable) — defers to Haytham's
  pre-send review.
- **Gate 1:** Pass — solo operator throughout ("I", "Donna will confirm your preferred time personally",
  single-person brand, personal @dbdonnabrown.com address). No agency/gatekeeper signals.
- **Lane:** Lane 1 (felt leak) — a verified, visible defect at the point of purchase.

## Findings — reasoning

> The **canonical, structured** copy of each finding lives in Airtable (`Findings` table): rank, status,
> depth, type, innocent explanation, evidence path. This section carries the *reasoning* — why it's deep
> vs shallow, why it stings, what was ruled out. Don't duplicate the fields here; they will drift.

**Rank 1 — Core Blueprint checkout upsells the bundle that already contains it**
Depth: DEEP · Type: order-bump / pricing logic error
Innocent explanation: the Stripe payment-link cross-sell was set to promote the highest-value product
to lift order value, without noticing the bundle already includes the course the buyer is on — an easy
Stripe "add to order" config oversight, not carelessness.
Why it matters: it sits at the moment of highest intent — the Core Blueprint checkout offers "The
Complete Growth Bundle" (AED 1,997) as an order-bump add-on, but the bundle already contains Your Core
Blueprint, so anyone who adds it pays for the foundation course twice (AED 597 + AED 1,997) right when
they're handing over their card. Show/Fix/Done from the walk's Loom skeleton: Show the Core Blueprint
Stripe checkout (buy.stripe.com/7sY14n1RXdYLbgRgBFgYU03), the "Add to your order → The Complete Growth
Bundle AED 1,997" bump, then the bundle page listing Core Blueprint as included. Fix: in Stripe, swap
that add-on for an upgrade that charges only the difference (or remove the bundle bump on the course
that's already inside it) and rename the promoted product so it doesn't duplicate the item. Done state:
a Core Blueprint buyer sees a bump that adds new value (or a true upgrade price), never the same course
billed twice.
Evidence: [`finding-1.png`](./evidence/finding-1.png) (not yet promoted)

**Rank 2 — "Save 35%" badge overstates the real discount** *(RESERVED — call bait, never emailed)*
Depth: SHALLOW · Type: pricing/copy accuracy
Innocent explanation: a round marketing number typed in before the prices were finalized.
Why it matters: AED 2,797 → AED 1,997 is about 29% off (and the four courses list at AED 2,988, so even
the struck-through anchor is off) — a buyer doing the math before purchase catches the gap.

**Rank 3 — Course names don't match across the funnel** *(RESERVED — call bait, never emailed)*
Depth: SHALLOW · Type: naming consistency
Innocent explanation: courses renamed during a rebuild, with the bundle page not caught up.
Why it matters: the foundation course is "Your Core Blueprint" on the cards/checkout but "The Inner
Blueprint" in the bundle comparison table/curriculum, and the fourth course is "Calm is a Superpower" on
the cards but "Steadiness Within" in the bundle table/hierarchy copy — a buyer comparing pages can't be
sure they're the same products.

**Rank 4 — Stripe checkout branded "Coaching Business," not Donna Brown** *(RESERVED — call bait, never emailed)*
Depth: SHALLOW · Type: trust/branding
Innocent explanation: the Stripe account business name was never set to her brand.
Why it matters: a small trust drop the moment the card comes out.

## SMYKM Hook

`no hook found in public evidence` — re-checked 2026-07-17 (haytham-hook-finder): LinkedIn newest post
still Jan 25 2023 (3yr old), Instagram @mindset_maestro shows nothing in the last 365 days — every
channel remains dormant since 2023-2024, nothing new to work from — draft opens on the finding alone.

That is a valid resolution, not a failure.

---

*Email history lives in Airtable (`Touches` table) — every send and reply, verbatim.
Price discovery answer and anchor live on the Airtable `Leads` record.
Neither is duplicated here.*
