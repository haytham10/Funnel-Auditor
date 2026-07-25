# Libby Salord McLean

<!-- airtable-record: TBD -->
> **Site:** https://www.libbysalord.com/nannytraining · **Profile:** https://www.instagram.com/libbysalord_coach/
> **Walked:** 2026-07-24 · **Slug:** `libby-salord-mclean`

---

## Overview

Libby Salord McLean — Resilience & EFT/nervous-system coach in Dubai, solo founder ("Pocket Wellness"), Wix site. Coach Type: Health, Life. Sells across several tiers: a 299 AED in-person Nanny & Caregiver Training workshop (the sourced Site URL / flagship offer), 1:1 "Coaching Containers" (2,700-6,600 AED), a self-guided "Reclaim Your Calm" audio series (159 AED, Stripe checkout), a "Free 30 Minute Clarity Call" (Google Calendar booking), and a small digital shop (affirmation cards, workbook, 98-122 AED, Wix cart). Audience: Instagram @libbysalord_coach, 1,511 followers (LinkedIn alone is 1,171, under floor — IG is her largest channel), posting several times a week, most recent post July 23, 2026.

## Funnel Walk

- Stop 1 (Entry — /nannytraining) — Loads clean, one clear workshop story, price shown (299 AED). No dead links.
- Stop 2 (Freebie — /reclaimyourcalm) — Found via site map (not linked from the entry page's raw HTML — a Wix menu item). Real product, real Stripe checkout (buy.stripe.com), confirmed live (curl 200). Not a leak.
- Stop 3 (Offer/sales — /nannytraining, /wellnesscoaching) — Both pages state price and value clearly in well under 10 seconds. But both pages' primary "buy" buttons are mailto: links (see Stop 4) — a confusing top/bottom CTA mismatch on /nannytraining: the upper "Enquire today" button's pre-filled email subject reads "...for the training for Dec/beyond" while the lower "Book here" button's subject has no date at all ("I want to book my nanny into the training"). A visitor reading both could reasonably conclude the earliest opening is December (5 months out).
- Stop 4 (Checkout/booking) — /nannytraining "Enquire today" and "Book here", and /wellnesscoaching "Your healing journey starts here" (the 2,700-6,600 AED containers) are all mailto:hello@libbysalord.com?subject=... links — no scheduler, no checkout, no payment link. This is despite her running a fully working Google Calendar booking link ("Free 30 minute Clarity Call", confirmed live) and a fully working Stripe checkout (Reclaim Your Calm) elsewhere on the same site. The /shop product page (busymumsworkbook, 108 AED) has a normal working "Add to Cart" Wix flow — no issue there.
- Stop 5 (Audience ownership) — a machine flag of "no email capture anywhere" was rejected — every page carries a live footer opt-in form ("Subscribe to my mailing list... Join my community"), visually confirmed on all four crawled pages. Not a finding.

## Evidence

- **Site vision pass:** `VISION PASS: COMPLETE — 7 of 7 required images confirmed read`
- **Pasted evidence:** none — crawl-only walk (one extra screenshot, reclaimyourcalm desktop, pulled for context on the freebie stop, not part of the required manifest)
- **Screenshots:** none promoted yet — see per-finding notes below

## Gates

- **Gate 0:** Pass — UAE-based (LinkedIn ae.linkedin.com/in/libby-salord-mclean, IG bio "mums in Dubai"); funnel exists (299 AED workshop + 2,700-6,600 AED containers + working Stripe/Wix checkouts elsewhere); activity floor clears (IG post July 23, 2026); audience floor clears (1,511 IG followers, re-confirmed via `apify ig --mode details`, a hard number).
- **Gate 1:** Pass — solo founder, first-person "About Me" copy, own face in all photos, no team/agency language anywhere in the crawl.
- **Lane:** Lane 1 (open) — felt leak survives both filters.

## Findings — reasoning

**Rank 1 — highest-value offers can only be booked by hand-writing an email**
Depth: SHALLOW (per archive label) · marked UNUSED in the bank
Type: manual-only checkout (mailto: link in place of a scheduler/checkout, on offers where real tooling already exists elsewhere on the same site)
Innocent explanation: she likely wired up Stripe/Calendly for the newer, simpler offers (audio series, clarity call) first and just hasn't gotten around to pointing the same links at her older flagship pages yet.
Why it matters: her two highest-value offers (299 AED nanny workshop, 2,700-6,600 AED coaching containers) can only be bought/booked by hand-writing an email to a mailto: link — no checkout, no scheduler — even though she already runs a live Stripe checkout and a live Google Calendar booking link for her lower-ticket offers on the same site. Independently verified: the mailto-only checkout for the 299 AED nanny workshop and the 2,700-6,600 AED coaching containers was confirmed in the raw page HTML, contrasted directly against the live Stripe checkout (curl 200) and the live Google Calendar link (curl 200) elsewhere on the site.
Loom skeleton (not sent, kept for a walkthrough offer): show the "Book here" button on /nannytraining (and the "Your healing journey starts here" button on /wellnesscoaching), clicked live to show the mailto: draft it opens instead of a booking page; fix would be pointing both buttons at the same Google Calendar link already live on /wellnesscoaching ("Free 30 minute Clarity Call"), or wiring up a dedicated Wix Bookings service for each paid offer; done state is clicking "Book here" opening a live calendar with real available slots instead of a blank email draft, no typing required to book.
Evidence: none promoted yet.

**Rank 2 — the nanny-training page's own two CTAs disagree on availability** *(UNUSED — reserve finding)*
Depth: SHALLOW
Type: copy inconsistency (conflicting pre-filled CTA subject lines)
Innocent explanation: leftover subject text from when December was the only open cohort, never updated once new dates opened.
Why it matters: the top "Enquire today" button's pre-filled subject says "...for the training for Dec/beyond" while the bottom "Book here" button's subject has no date restriction — a visitor could read the top button and conclude the next opening is 5 months away.
Evidence: none promoted yet.

**Rank 3 — no path connects the low-ticket shop to the high-ticket offers** *(RESERVED — call bait, never emailed)*
Depth: DEEP
Type: structural ladder gap (no order bump/upsell from proven buyers to flagship offers)
Innocent explanation: the shop and the coaching/workshop pages were clearly built at different times, as separate pieces, not as one connected ladder.
Why it matters: no automated path connects her frictionless self-serve digital shop (98-159 AED cards/workbook/audio, real Stripe/Wix checkout) to her two highest-margin offers (299 AED workshop, 2,700-6,600 AED containers) — a buyer who just proved she'll pay Libby money gets no order bump, upsell, or nudge toward the higher-ticket work; every one of those higher-value sales depends entirely on Libby personally catching and closing a manual email.
Evidence: none promoted yet.

One machine flag was rejected on the vision pass and not banked: "no email capture anywhere" (a footer opt-in form is visible on every page screenshot).

## SMYKM Hook

`Saw you've teamed up with Mamahood to run your Conscious Nanny Training regularly out of their Al Wasl Road centre now, with August dates already on the calendar` — **WORK** — source: https://www.instagram.com/p/DbFSj_PNm6F/

---

*Email history lives in Airtable (`Touches` table) — every send and reply, verbatim.
Price discovery answer and anchor live on the Airtable `Leads` record.
Neither is duplicated here.*
