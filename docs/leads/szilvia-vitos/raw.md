<!--
VERBATIM ARCHIVE — DO NOT EDIT
Source: Notion page 3a0382c8-4585-8157-82c7-c151df23108d
Fetched: 2026-07-25T13:41:16Z
This is the unparsed original. The structured copy lives in Airtable
(Touches / Leads). If a parse is ever wrong, this is the source of truth.
-->

## Overview
Szilvia Vitos runs LIVVITY ([livvity.coach](http://livvity.coach)), a solo leadership/wellbeing coaching practice in Dubai on WordPress (Avada/Fusion). She sells a cohort-based "Transformational Leadership Wellbeing Program" (group), 1:1 leadership-wellbeing coaching in 6-session packages, corporate training (partnership with Soha Chahine Coaching = delivery only), and workshops. 15 years corporate leadership before coaching; CTNC-certified. Audience 10,275 on LinkedIn. Own face and story throughout — solo operator.
## Funnel Walk
- Stop 1 (Entry / group-program page) — hero + two teal CTAs both reading "Enrollment Closed, Join The Priority List!" — the page's primary and only above-content CTA.
- Stop 2 (Freebie) — none. No opt-in / lead magnet anywhere in the crawled funnel.
- Stop 3 (Offer/Sales) — group-program, 1:1 coaching, leadership-coaching, workshops. No price shown on any (consultative model: "Book Your FREE Consultation" footer form on every page). Group program is closed.
- Stop 4 (Checkout) — only working paid checkout attempt is the workshop's "Reserve My Seat" → [livvity.shop](http://livvity.shop) / [livvity.myshopify.com](http://livvity.myshopify.com), both dead (see Findings). LeadConnector discovery-call booker is live but books a FREE call.
- Stop 5 (Audience ownership) — WordPress contact form only; no email list opt-in. Depends on LinkedIn reach.
## Evidence
- Site vision pass: VISION PASS: COMPLETE — 9 of 9 required images confirmed read
- Pasted evidence: none — crawl-only walk.
- Machine flags rejected in the vision pass: 2 — repeated-navbar mid-page on coaching/leadership fullPage captures (artifact, not layout breakage); "no visible pricing" as a standalone opener (consultative — demoted, not banked).
- Finding #1 evidence: evidence/szilvia-vitos/screenshots/livvity_coach_group-program_desktop.png + evidence/szilvia-vitos/_firecrawl_raw/1.html (both "Join The Priority List" anchors have href="[https://livvity.coach/group-program/#](https://livvity.coach/group-program/#)", no modal/form attrs) + cta-probe on group-program returned cta_clicks: \[\].
- Finding #2 evidence: evidence/szilvia-vitos/screenshots/livvity_coach_livvity-workshop_desktop.png + evidence/szilvia-vitos/_firecrawl_raw/4.html ("Reserve My Seat" → [https://livvity.shop/collections/workshops](https://livvity.shop/collections/workshops) and [https://livvity.myshopify.com/a/bundles/checkout/package-4x-4icu](https://livvity.myshopify.com/a/bundles/checkout/package-4x-4icu)). [livvity.shop](http://livvity.shop) fails DNS (Firecrawl DNS error + curl 502); [livvity.myshopify.com](http://livvity.myshopify.com) returns HTTP 423 (store locked).
- Finding #3 evidence: evidence/szilvia-vitos/screenshots/api_leadconnectorhq_com_widget_booking_qwDroUFTvzCX3IOjT4rn_desktop.png (Time zone field reads "GMT-04:00 America/New_York (EDT)", slots 6:00–9:30 AM).
- Independent verification: VERIFIED — both "Enrollment Closed, Join The Priority List!" anchors resolve to href="[https://livvity.coach/group-program/#](https://livvity.coach/group-program/#)" (bare # fragment, no onclick/data-modal/data-popup attrs) in _firecrawl_raw/1.html (lines 73, 87); both buttons render on livvity_coach_group-program_desktop.png. Dead waitlist CTA confirmed. Held at Qualifying — email gate unmet (Email Verified unchecked).
## Gates
Gate 0: Pass — UAE base Dubai (About page: Burj Al Arab imagery, "life & wellness coach" Dubai; confirmed at pre-flight); funnel exists (real paid coaching ladder — broken purchase paths are the leak, not a disqualifier); activity confirmed at pre-flight (weekly LinkedIn cadence through 2026-06-15); audience 10,275 LinkedIn.
Gate 1: Pass — solo founder. Own face, own story ("My Story"), single-person About page. Soha Chahine partnership is corporate-delivery only, not a gatekeeper.
## Lane + Finding
- Lane 1 (felt leak) — warm interest on the flagship program page is captured nowhere.
- Finding (bank #1): The group-program page invites visitors to "Join the Priority List to be the first one to know when doors are opening again," but both "Enrollment Closed, Join The Priority List!" buttons are dead anchors (href ends in `#`, no form, no popup) — a warm visitor who wants on the waitlist cannot leave their name.
- Innocent explanation: the priority-list button was almost certainly meant to open a signup form/popup that was never wired (or a form plugin broke on the WordPress rebuild), so she likely doesn't realize the waitlist collects nothing.
## Findings Bank
1. The group-program page's only CTA — "Enrollment Closed, Join The Priority List!" (twice) — is a dead anchor to `.../group-program/#`; the waitlist she actively promotes captures nobody. — innocent: signup form/popup never wired or plugin broke on the rebuild.
2. The workshop page's "Reserve My Seat" points to [livvity.shop](http://livvity.shop) (dead domain, DNS fails) and a [livvity.myshopify.com](http://livvity.myshopify.com) checkout that returns 423 (store locked) — the workshop buy path is broken end to end. — innocent: she migrated or closed the Shopify store and the workshop page still points at the old links.
3. The discovery-call booker (the one working conversion path) defaults to America/New_York (EDT) and only shows 6:00–9:30 AM slots — a Dubai visitor booking a Dubai coach sees US-morning times at the exact step that works. — innocent: the LeadConnector calendar's default timezone was never switched off the account's original US setting.
## Loom Skeleton
- Show: [livvity.coach/group-program/](http://livvity.coach/group-program/) — both teal "Enrollment Closed, Join The Priority List!" buttons; click one on-screen to show it just jumps to top and collects nothing.
- Fix: point those buttons at a simple 1-field email capture (a Fusion form or the LeadConnector waitlist form) so interested leads land on a list for the next cohort.
- Done state: clicking "Join the Priority List" opens a name+email form and the next cohort launches to a warm list instead of from zero.
## SMYKM Hook
SMYKM hook: Your post this morning about walking away from the villa deal because 'two scared people couldn't trust each other' — then landing the right place in under 24 hours through the one agent you trusted. That line stuck: people do business with people they trust, and it's the whole game. — LIFE — source: [https://www.linkedin.com/posts/szilviavitos_our-lease-is-up-end-of-september-our-landlord-activity-7484879898998788096-Fpa0](https://www.linkedin.com/posts/szilviavitos_our-lease-is-up-end-of-september-our-landlord-activity-7484879898998788096-Fpa0)
## Email Thread Log
\[2026-07-21\] — Touch #1 — Subject: "the villa deal" — Sent
Cold opener sent via Inbox 1, opening on the SMYKM hook and the Lane 1 finding (bank #1) per the row's Notes.
Reply: No reply
Next: 2026-07-24 — cold Touch 2 due (must carry the next unused Findings Bank entry, the Loom offer, or a disambiguating question — never a bare bump)
## Price Discovery
