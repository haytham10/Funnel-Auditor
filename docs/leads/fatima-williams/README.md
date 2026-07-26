# Fatima Williams

<!-- airtable-record: TBD -->
> **Site:** https://www.fatimawilliams.me/ · **Profile:** https://www.linkedin.com/in/dreamcareercoach/
> **Walked:** 2026-07-19 · **Slug:** `fatima-williams`

---

## Overview

Fatima Williams — Career Strategist & Executive Coach, founder of Dream Career Freedom (DCF) Academy,
Dubai. Career/Leadership coach for senior professionals and executives. Custom-built site
(fatimawilliams.me) with the offer ladder on TagMango. Main offer: a tiered coaching ladder (Silver
90-day / Gold 6-month / Diamond 12-month, monthly AED pricing) plus a free live "LinkedIn Co-Pilot
Bypass" workshop funnel, a $14.99 "121 with Fatima" pre-clarity call trip-wire, and a DCF Resume Co-Pilot
AI tool. Audience: 45,000+ LinkedIn followers, 22,000+ LinkedIn newsletter subscribers, host of The
Intentionality Series podcast; featured in Fast Company ME, BizCatalyst 360, American Diversity Report.

## Funnel Walk

- Stop 1 (Entry — fatimawilliams.me) — Clean single-page site, narrows to two CTAs (free workshop /
  clarity call). No dead end. Fine.
- Stop 2 (Freebie/opt-in) — The free live workshop IS the lead magnet (AED 99 → FREE), plus a "Know Your
  Brand Score" survey. Reachable, captures details. Fine.
- Stop 3 (Offer/pricing) — The flagship pricing section "Choose the Level That Matches Your Ambition"
  renders "AED ___" (literal blank placeholder) as the price on ALL THREE tiers — Silver, Gold, Diamond.
  Confirmed in raw HTML AND the rendered desktop screenshot (not a render artifact). This is the Lane 1
  finding.
- Stop 4 (Checkout/booking) — Workshop registration (TagMango) and the $14.99 "121 with Fatima" checkout
  both render fully and work — payment form, methods, live. Diamond's "by application only" tier routes
  its only CTA ("Book Your Fit Call") to that same $14.99 impulse checkout (secondary finding). Webinar
  date 21 Jul 2026 is upcoming (2 days out) — NOT stale.
- Stop 5 (Audience ownership) — Owns a 22,000+ LinkedIn newsletter list + podcast. Machine "no owned
  list / fully rented" flag is FALSE — rejected.

## Evidence

- **Site vision pass:** `VISION PASS: COMPLETE — 8 of 8 required images confirmed read`
- **Pasted evidence:** none — crawl-only walk. Machine flags rejected in the vision pass: 3 — "no owned
  list" (has 22K newsletter), workshop-form-empty (JS iframe render artifact, has fallback link),
  no-email-capture-mechanism (vitamin, not felt cost). Independent verification: VERIFIED — flagship
  pricing section renders literal "AED ___" on all three tiers (Silver/Gold/Diamond) confirmed on
  evidence/fatima-williams/screenshots/www_fatimawilliams_me_desktop.png (rendered) AND
  evidence/fatima-williams/_firecrawl_raw/1.html (static HTML).
- **Screenshots:** none promoted yet — see per-finding notes below

## Gates

- **Gate 0:** Pass — UAE-based (Dubai, trained at University of Dubai, UAE/GCC focus); funnel confirmed
  (working workshop + $14.99 checkout + tiered ladder); activity (workshop launch dated 21 Jul 2026,
  posted ~2d ago); audience 46,038 LinkedIn.
- **Gate 1:** Pass — solo operator, own face, own story, own name throughout ("I'm Fatima Williams…"),
  single-person About. No gatekeeper.
- **Lane:** Lane 1 (felt leak) — a provable blank on the flagship pricing section of a real committed
  operator.

## Findings — reasoning

> The **canonical, structured** copy of each finding lives in Airtable (`Findings` table): rank, status,
> depth, type, innocent explanation, evidence path. This section carries the *reasoning* — why it's deep
> vs shallow, why it stings, what was ruled out. Don't duplicate the fields here; they will drift.

**Rank 1 — Pricing section shows a literal "AED ___" placeholder on all three tiers**
Depth: DEEP · Type: blank placeholder at the buy-decision moment
Innocent explanation: prices look deliberately gated behind the workshop ("Join the Workshop to Learn
More"), so the "AED ___" reads like a build-template placeholder left in when the page published rather
than an intended display.
Why it matters: the pricing section where a senior buyer chooses their tier shows "AED ___" instead of a
price on all three cards (Silver, Gold, Diamond) — the most considered visitors reach the buy-decision and
see a blank where the number should be. Show/Fix/Done from the walk's Loom skeleton: Show
fatimawilliams.me pricing section ("Choose the Level That Matches Your Ambition") — the three tier cards
each reading "AED ___/month". Fix: fill the real monthly figure into each tier card, or if pricing is
intentionally gated, swap "AED ___" for "By application" / "Priced in the workshop" so a blank never
renders. Done state: every tier card shows a deliberate price line instead of "AED ___" — a senior
visitor at the decision point sees a finished, premium pricing section.
Evidence: [`finding-1.png`](./evidence/finding-1.png) (not yet promoted)

**Rank 2 — Diamond's only CTA routes to a $14.99 impulse checkout** *(RESERVED — call bait, never emailed)*
Depth: SHALLOW · Type: premium-tier framing drop
Innocent explanation: the paid $14.99 pre-clarity call is an intentional qualification step and the
checkout just carries its platform's generic scarcity copy.
Why it matters: Diamond, her "by application only" executive tier, sends its only CTA ("Book Your Fit
Call") to a $14.99 impulse checkout carrying "4 seats left, hurry up" — the premium framing drops at the
click for her highest-value buyer.

## SMYKM Hook

`Her post today reframing the job search as a "visibility gap, not a skills gap" — same person, same
experience, different positioning, different outcome — and visibility as a skill you can learn` —
**WORK** — source:
https://www.linkedin.com/posts/dreamcareercoach_careercoach-careeradvice-copilotcoach-activity-7484879055323037696-CaRc

---

*Email history lives in Airtable (`Touches` table) — every send and reply, verbatim.
Price discovery answer and anchor live on the Airtable `Leads` record.
Neither is duplicated here.*
