# Rita Baki

<!-- airtable-record: TBD -->
> **Site:** http://ritabaki.com · **Profile:** https://www.instagram.com/rita_baki
> **Walked:** 2026-07-17 · **Slug:** `rita-baki`

---

## Overview

Rita Baki is a Dubai-based Neuro Coach & Master Trainer (emotional intelligence, NLP, clinical hypnotherapy) with 26K Instagram followers (@rita_baki). She runs her own branded site (ritabaki.com, Squarespace) offering 1:1 sessions ($190-$817), corporate training, and certification courses; is separately listed with AED pricing (750-7,000) on The Holistic Culture marketplace (the Source Channel lead here); and holds professional affiliations with The Flow Space (Head of Corporate Wellness) and Keyani Wellness. Real credentials (ICF UAE, ABH, NFNLP), real paid ladder, no gatekeeper found.

## Funnel Walk

- Stop 1 (Bio — ritabaki.com) — Clean single CTA, "Book your free discovery call now" narrows to one action immediately.
- Stop 2 (Freebie) — None found on either her own site or the marketplace listing — goes straight to consult/booking (vitamin, not flagged as opener).
- Stop 3 (Offer/Sales) — ritabaki.com/one-on-one-sessions shows clear USD pricing ($190-$817) in under 10 seconds. Separately, The Holistic Culture listing's header teaser reads "Price on request / From" directly above the Book button, while the booking widget two sections below on the SAME page publishes exact AED prices (750/3,450/5,500/7,000).
- Stop 4 (Checkout/Booking) — The hero CTA on her own site ("Book your free discovery call now") — her single highest-intent click — lands on /purchase-form-1, titled "REGISTER FORM": a bare Name/Email/Phone form, no calendar, no time-slot picker, no confirmed appointment. Confirmed on desktop and mobile. By contrast, the marketplace's own multi-step booking widget (session type → date picker) works cleanly; clicking a paid session type enables Continue and advances to a real calendar with open dates.
- Stop 5 (Audience ownership) — Owns her own IG (26K) and her own domain, but paid-session pricing is fragmented across at least 3 platforms (her own site in USD, The Holistic Culture in AED, plus unpriced listings on Flow Space and Keyani Wellness) with no single unified booking/pricing surface.

## Evidence

- **Site vision pass:** `VISION PASS: COMPLETE — 8 of 8 required images confirmed read`
- **Pasted evidence:** none attached — page body was blank on fetch, crawl-only walk.
- **Screenshots:** none promoted at original walk time — see per-finding notes below. Two machine flags were rejected in the vision pass, both from the same root cause — "no-html-provided" (the ingest manifest omitted raw HTML for the ritabaki.com pages, so the machine text-checker mis-flagged Stop 1 as "blocked" and Stop 3 as "no price shown"; both screenshots directly confirm the pages load cleanly and show real USD prices).

**Re-walked 2026-07-25** (evidence-persistence pass): re-fetched the homepage, the old
`/purchase-form-1` path, the Calendly destination the primary CTA now points to, her own
`/one-on-one-sessions` page, and The Holistic Culture marketplace listing live via Firecrawl.
Rank 1 (the load-bearing, already-emailed finding) is **RESOLVED** — she has since wired a real
Calendly scheduler behind the "Book your free discovery call now" CTA. Rank 2 is also
**no longer present**, but as a side effect of a full platform migration on The Holistic Culture's
side, not a targeted fix. Rank 3 is **still present**, unchanged. Fresh screenshots:
[`./evidence/`](./evidence/) (promoted) and the full re-walk capture set at
[`../../../evidence/rita-baki/screenshots/`](../../../evidence/rita-baki/screenshots/).

## Gates

- **Gate 0:** Pass — UAE-based (Dubai; also "Dubai Hills" per Flow Space listing), funnel confirmed (real paid sessions on ritabaki.com + AED packages on The Holistic Culture, both with working booking mechanics), activity floor already confirmed at qualify stage (327 IG posts, recent conference-speaking reel), audience floor confirmed (26,000 IG).
- **Gate 1:** Pass — individually reachable via her own site/IG/LinkedIn, own face and own story throughout; multi-venue professional affiliations (Flow Space, Keyani Wellness) are day-job/partner listings, not a team wall blocking direct contact.
- **Lane:** Lane 1 (felt leak) on a committed, credentialed buyer with a real paid ladder.

## Findings — reasoning

> The **canonical, structured** copy of each finding lives in Airtable (`Findings` table):
> rank, status, depth, type, innocent explanation, evidence path. This section carries the
> *reasoning* — why it's deep vs shallow, why it stings, what was ruled out. Don't duplicate
> the fields here; they will drift.

**Rank 1 — the site's highest-intent CTA leads to a bare form, not a booking**
Depth: DEEP · Type: dead-end conversion path behind the primary CTA
Innocent explanation: probably just the default Squarespace form block left in place before a real scheduler (Calendly/Acuity) got wired in — an easy swap, not a sign anything else is wrong.
Why it matters: her own site's primary CTA, "Book your free discovery call now," leads only to a bare contact form with no scheduler — the highest-intent click on her own funnel doesn't actually book anything. A visitor who is ready to act fills in a form and waits, instead of confirming a time on the spot.
Re-walked 2026-07-25: **no longer present as of 2026-07-25** — original evidence lost
(pre-persistence). The homepage's "Book your free discovery call now" CTA now links to
`https://calendly.com/ritabaki/intro-call?month=2026-07`, a live Calendly scheduler showing a real
July 2026 date grid ("Select a Date & Time"), not `/purchase-form-1`. The old bare Name/Email/Phone
form still technically exists at `ritabaki.com/purchase-form-1` (confirmed still live, same content
as originally flagged) but it is now orphaned — nothing on the site links to it anymore, so it is no
longer in the CTA's path. This finding should not be referenced in further outreach to this lead.
Evidence (not promoted — finding is resolved, per the honesty rule): raw re-walk captures at
`evidence/rita-baki/screenshots/homepage_rewalk_20260725.png`,
`calendly_scheduler_rewalk_20260725.png`, and `purchase_form_1_orphaned_rewalk_20260725.png`.

**Rank 2 — marketplace listing's price teaser contradicts its own booking widget** *(RESERVED — call bait, never emailed)*
Depth: SHALLOW · Type: self-contradicting price signal
Innocent explanation: likely a platform template pulling the "from" price off the free consultation's blank price field instead of the true lowest paid tier.
Why it matters: The Holistic Culture marketplace listing's header price teaser reads "Price on request / From" directly above the Book button, while the booking widget two sections below the SAME page publishes exact AED prices (750-7,000) — price-sensitive visitors who read "on request" as "expensive" may bounce before ever scrolling to the real, affordable AED 750 entry price.
Re-walked 2026-07-25: **no longer present as of 2026-07-25** — original evidence lost
(pre-persistence). The Holistic Culture has rebuilt Rita's listing on an entirely different
platform (a Shopify Hydrogen storefront at `theholisticculture.com/en-us/products/rita-baki`,
replacing whatever booking-widget layout was there at original walk time). The page now shows a
"Select Service" dropdown; the header price updates live to match whichever service is selected
(confirmed AED 0.00 for "Free Consultation," AED 750.00 for "Therapy Session | 60mins" — matching
the AED figures originally recorded). No "Price on request" text appears anywhere on the current
page. This looks like a byproduct of a platform migration, not a targeted fix to the price-teaser
bug specifically — flagging in case the same defect reappears if the listing changes again.
Evidence (not promoted — finding is resolved, per the honesty rule): raw re-walk captures at
`evidence/rita-baki/screenshots/holisticculture_default_load_rewalk_20260725.png` and
`holisticculture_therapy_selected_rewalk_20260725.png`.

**Rank 3 — session pricing is fragmented across platforms with no single source of truth** *(RESERVED — call bait, never emailed)*
Depth: SHALLOW · Type: cross-platform price inconsistency
Innocent explanation: natural byproduct of partnering with multiple wellness venues, not a deliberate inconsistency.
Why it matters: pricing splits across platforms — USD on her own site ($190-$817), AED on The Holistic Culture (750-7,000), and unpriced listings on The Flow Space and Keyani Wellness — a prospect comparing her across channels sees different numbers in different currencies.
Re-walked 2026-07-25: **still present.** `ritabaki.com/one-on-one-sessions` still shows USD pricing
(Hypnotherapy "From 328.00$", Sound Healing "190.00$", Coaching "From 817.00$" — prices moved
slightly from the original $190-$817 range but the currency mismatch is unchanged), while The
Holistic Culture's now-rebuilt listing shows AED (0-750+ per the Select Service dropdown, real
figures confirmed for the free and 60-min tiers). The two platforms still speak different
currencies for the same person's services.
Evidence: [finding-3.png](./evidence/finding-3.png) (her own USD pricing page); AED-side
comparison at `evidence/rita-baki/screenshots/holisticculture_therapy_selected_rewalk_20260725.png`.

The Loom skeleton drafted for Rank 1 shows ritabaki.com's homepage hero, "Book your free discovery call now" button, click-through to ritabaki.com/purchase-form-1. Fix: replace the destination with an embedded live scheduler (Calendly/Acuity or Squarespace's own scheduling block) so the button's promise matches what happens when it's clicked. Done state: clicking "Book your free discovery call now" lands on a live calendar with open slots; a visitor picks a time and gets an instant confirmation instead of submitting a form and waiting. This finding was ultimately delivered as a Loom walkthrough (plus a second coach's site shown live with the same fix applied) rather than as plain email copy — see the note below.

## SMYKM Hook

`her Jun 22 IG post marking 50, quoting Carl Jung ("the afternoon of life must also have a significance of its own") — "I have survived enough, loved enough, lost enough, and learned enough to trust"` — **LIFE**

---

*Email history lives in Airtable (`Touches` table) — every send and reply, verbatim. This lead's
raw archive carries an unusually rich five-touch thread (a warm reply, a Loom walkthrough offer
and delivery, and a price-discovery exchange) — all of that detail is preserved verbatim in the
`.raw.md` archive and becomes Airtable Touches rows; none of it is duplicated here.
Price discovery answer and anchor live on the Airtable `Leads` record.
Neither is duplicated here.*
