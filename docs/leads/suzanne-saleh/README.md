# Suzanne Saleh

<!-- airtable-record: TBD -->
> **Site:** https://www.suzannesaleh.com/health-coaching · **Profile:** https://www.instagram.com/suzannesalehwellness, https://ae.linkedin.com/in/suzanne-saleh-b0b70b22
> **Walked:** 2026-07-17 · **Slug:** `suzanne-saleh`

---

## Overview

Suzanne Saleh, Dubai-based Integrative Nutrition health coach for women 40+ (perimenopause, plant-based living, weight loss). Runs on Wix. Paid ladder: 369 Liver Cleanse Kit (AED495), 30-Day Body Reset Program (Group AED1500 / Private AED2250, via Stripe + Tabby), and 1-month coaching (1500 AED / $400). Free 30-min consultation booking is the entry mechanism. Audience: 4,868 followers on Instagram.

## Funnel Walk

- Stop 1 (Bio/entry) — /health-coaching landing page links out to consultation, services, and both programs — clean.
- Stop 2 (Freebie) — no dedicated opt-in/lead magnet page found; the free consultation booking form is the only entry mechanism.
- Stop 3 (Offer/Sales) — /30daybodyresetprogram is the live, current sales page (AED1500/2250, Apple Pay/Google Pay/Card/Tabby badges shown). A second, stale route to the same program — /event-details/30-day-body-reset-program-group, dated Jul 2022 — is still reachable and shows "Registration is closed."
- Stop 4 (Checkout) — both Stripe "Get Started" links (Group and Private) resolve to a Stripe error page: "Something went wrong — There are no valid payment methods available for this session. Please contact the merchant." Confirmed on desktop and mobile, both tiers.
- Stop 5 (Audience ownership) — email capture present (newsletter signup on /about + consultation form) — she owns a list, not fully rented-reach dependent.

## Evidence

- **Site vision pass:** `VISION PASS: COMPLETE — 16 of 16 required images confirmed read`
- **Pasted evidence:** none attached — crawl-only walk
- **Screenshots:** none promoted yet — see per-finding notes below
- **Machine flags rejected in the vision pass:** 2 — JS-only button destinations (BUY NOW / ENTER NOW on /services, /coaching) unconfirmed, no click-through evidence; "loadbalancer.visitor-analytics.io is blocked" banner appearing in scraped text is a crawler ad-blocker artifact, not a real visitor issue.

## Gates

- **Gate 0:** Pass — UAE-based (Dubai-UAE address in site footer + LinkedIn + IG bio), funnel present (30-Day Body Reset Program + coaching + liver cleanse kit, real Stripe checkout), audience 4,868 (IG) — confirmed at qualify-leads stage, reconfirmed against the full crawl.
- **Gate 1:** Pass — solo operator, no team/gatekeeper visible anywhere in the crawl.
- **Lane:** Lane 1 (felt leak) — a live, currently-priced offer's actual checkout is broken for both tiers, on both devices.

## Findings — reasoning

> The **canonical, structured** copy of each finding lives in Airtable (`Findings` table): rank, status, depth, type, innocent explanation, evidence path. This section carries the *reasoning* — why it's deep vs shallow, why it stings, what was ruled out. Don't duplicate the fields here; they will drift.

**Rank 1 — both Stripe checkout links for the flagship program error out**
Depth: DEEP · Type: Broken checkout on the current live offer, both tiers
Innocent explanation: Stripe's payment-methods toggle (Apple Pay/Google Pay/Card) likely got disabled or misconfigured for that account/session, not a deliberate choice.
Why it matters: both "Get Started" Stripe checkout links for the 30-Day Body Reset Program (Group AED1500 / Private AED2250) return "Something went wrong — there are no valid payment methods available for this session" on desktop and mobile. Loom framing: show suzannesaleh.com/30daybodyresetprogram, clicking "Get Started" under either Group or Private Program; the fix is reconnecting/re-enabling the Stripe payment methods (Apple Pay, Google Pay, Card, Tabby) for that checkout session; done state is clicking "Get Started" opening a real Stripe checkout with working payment options instead of "Something went wrong."
Evidence: not yet promoted — see [`suzanne-saleh.raw.md`](./suzanne-saleh.raw.md) for citation.

**Rank 2 — a 2022 event listing for the same program is still live and reachable** *(RESERVED — call bait, never emailed)*
Depth: SHALLOW · Type: Stale duplicate listing, dead-ended
Innocent explanation: an old Wix Events entry from a past cohort was never unpublished or redirected when the program moved to its current sales page.
Why it matters: the 2022 listing ("Batch 2," dated Jul 30 – Aug 29 2022) shows "Registration is closed" with no link forward to the current program page — a second, dead-ended path into the same offer.
Evidence: not yet promoted — see [`suzanne-saleh.raw.md`](./suzanne-saleh.raw.md) for citation.

## SMYKM Hook

SMYKM hook: no hook found in IG evidence (Apify pull returned profile only, no posts — likely private) — draft opens on the finding alone

---

*Email history lives in Airtable (`Touches` table) — every send and reply, verbatim.
Price discovery answer and anchor live on the Airtable `Leads` record.
Neither is duplicated here.*
