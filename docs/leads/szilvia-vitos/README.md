# Szilvia Vitos

<!-- airtable-record: TBD -->
> **Site:** https://livvity.coach/group-program/ · **Profile:** https://ae.linkedin.com/in/szilviavitos
> **Walked:** 2026-07-17 · **Slug:** `szilvia-vitos`

---

## Overview

Szilvia Vitos runs LIVVITY (livvity.coach), a solo leadership/wellbeing coaching practice in Dubai on WordPress (Avada/Fusion). She sells a cohort-based "Transformational Leadership Wellbeing Program" (group), 1:1 leadership-wellbeing coaching in 6-session packages, corporate training (partnership with Soha Chahine Coaching = delivery only), and workshops. 15 years corporate leadership before coaching; CTNC-certified. Audience 10,275 on LinkedIn. Own face and story throughout — solo operator.

Note: per the raw archive, this lead was held at **Qualifying** as of the walk — the email gate was unmet (Email Verified unchecked).

## Funnel Walk

- Stop 1 (Entry / group-program page) — hero + two teal CTAs both reading "Enrollment Closed, Join The Priority List!" — the page's primary and only above-content CTA.
- Stop 2 (Freebie) — none. No opt-in / lead magnet anywhere in the crawled funnel.
- Stop 3 (Offer/Sales) — group-program, 1:1 coaching, leadership-coaching, workshops. No price shown on any (consultative model: "Book Your FREE Consultation" footer form on every page). Group program is closed.
- Stop 4 (Checkout) — only working paid checkout attempt is the workshop's "Reserve My Seat" → livvity.shop / livvity.myshopify.com, both dead (see Findings). LeadConnector discovery-call booker is live but books a FREE call.
- Stop 5 (Audience ownership) — WordPress contact form only; no email list opt-in. Depends on LinkedIn reach.

## Evidence

- **Site vision pass:** `VISION PASS: COMPLETE — 9 of 9 required images confirmed read`
- **Pasted evidence:** none — crawl-only walk.
- **Screenshots:** none promoted yet — see per-finding notes below
- **Machine flags rejected in the vision pass:** 2 — repeated-navbar mid-page on coaching/leadership fullPage captures (artifact, not layout breakage); "no visible pricing" as a standalone opener (consultative — demoted, not banked).
- **Independent verification:** VERIFIED — both "Enrollment Closed, Join The Priority List!" anchors resolve to `href="https://livvity.coach/group-program/#"` (bare # fragment, no onclick/data-modal/data-popup attrs) in the raw Firecrawl HTML (lines 73, 87); both buttons render on the group-program desktop screenshot. Dead waitlist CTA confirmed.

## Gates

- **Gate 0:** Pass — UAE base Dubai (About page: Burj Al Arab imagery, "life & wellness coach" Dubai; confirmed at pre-flight); funnel exists (real paid coaching ladder — broken purchase paths are the leak, not a disqualifier); activity confirmed at pre-flight (weekly LinkedIn cadence through 2026-06-15); audience 10,275 LinkedIn.
- **Gate 1:** Pass — solo founder. Own face, own story ("My Story"), single-person About page. Soha Chahine partnership is corporate-delivery only, not a gatekeeper.
- **Lane:** Lane 1 (felt leak) — warm interest on the flagship program page is captured nowhere.

## Findings — reasoning

> The **canonical, structured** copy of each finding lives in Airtable (`Findings` table): rank, status, depth, type, innocent explanation, evidence path. This section carries the *reasoning* — why it's deep vs shallow, why it stings, what was ruled out. Don't duplicate the fields here; they will drift.

**Rank 1 — the "Join The Priority List" waitlist button is a dead anchor**
Depth: DEEP · Type: Dead waitlist CTA (the only capture on the flagship program page)
Innocent explanation: the priority-list button was almost certainly meant to open a signup form/popup that was never wired (or a form plugin broke on the WordPress rebuild), so she likely doesn't realize the waitlist collects nothing.
Why it matters: the group-program page invites visitors to "Join the Priority List to be the first one to know when doors are opening again," but both "Enrollment Closed, Join The Priority List!" buttons are dead anchors (href ends in `#`, no form, no popup) — a warm visitor who wants on the waitlist cannot leave their name. A `cta-probe` run on the page also returned zero CTA clicks, confirming the button does nothing live, not just in the static HTML. Loom framing: show livvity.coach/group-program/, both teal "Enrollment Closed, Join The Priority List!" buttons, clicking one on-screen to show it just jumps to top and collects nothing; the fix is pointing those buttons at a simple one-field email capture (a Fusion form or the LeadConnector waitlist form); done state is clicking "Join the Priority List" opening a name+email form so the next cohort launches to a warm list instead of from zero.
Evidence: `evidence/szilvia-vitos/screenshots/livvity_coach_group-program_desktop.png` + `evidence/szilvia-vitos/_firecrawl_raw/1.html` (both anchors, no modal/form attrs) — not yet promoted into this doc's evidence folder.

**Rank 2 — workshop "Reserve My Seat" points to a dead shop and a locked storefront** *(RESERVED — call bait, never emailed)*
Depth: DEEP · Type: Broken end-to-end purchase path
Innocent explanation: she migrated or closed the Shopify store and the workshop page still points at the old links.
Why it matters: "Reserve My Seat" points to livvity.shop (dead domain, DNS fails) and a livvity.myshopify.com checkout that returns HTTP 423 (store locked) — the workshop buy path is broken end to end.
Evidence: `evidence/szilvia-vitos/screenshots/livvity_coach_livvity-workshop_desktop.png` + `evidence/szilvia-vitos/_firecrawl_raw/4.html` — not yet promoted into this doc's evidence folder.

**Rank 3 — the one working conversion path defaults to a US timezone** *(RESERVED — call bait, never emailed)*
Depth: SHALLOW · Type: Un-localized scheduling default
Innocent explanation: the LeadConnector calendar's default timezone was never switched off the account's original US setting.
Why it matters: the discovery-call booker (the one working conversion path) defaults to America/New_York (EDT) and only shows 6:00–9:30 AM slots — a Dubai visitor booking a Dubai coach sees US-morning times at the exact step that works.
Evidence: `evidence/szilvia-vitos/screenshots/api_leadconnectorhq_com_widget_booking_qwDroUFTvzCX3IOjT4rn_desktop.png` — not yet promoted into this doc's evidence folder.

## SMYKM Hook

SMYKM hook: Your post this morning about walking away from the villa deal because 'two scared people couldn't trust each other' — then landing the right place in under 24 hours through the one agent you trusted. That line stuck: people do business with people they trust, and it's the whole game. — LIFE — source: [https://www.linkedin.com/posts/szilviavitos_our-lease-is-up-end-of-september-our-landlord-activity-7484879898998788096-Fpa0](https://www.linkedin.com/posts/szilviavitos_our-lease-is-up-end-of-september-our-landlord-activity-7484879898998788096-Fpa0)

---

*Email history lives in Airtable (`Touches` table) — every send and reply, verbatim.
Price discovery answer and anchor live on the Airtable `Leads` record.
Neither is duplicated here.*
