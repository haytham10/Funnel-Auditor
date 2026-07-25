<!--
VERBATIM ARCHIVE — DO NOT EDIT
Source: Notion page 3a0382c8-4585-81d3-b198-ca22f1a75677
Fetched: 2026-07-25T13:40:12Z
This is the unparsed original. The structured copy lives in Airtable
(Touches / Leads). If a parse is ever wrong, this is the source of truth.
-->

## Overview
Dr. Jamila Al Hosani is a solo Career & Leadership coach based in Dubai, running her practice through The Holistic Culture, a UAE coach/wellbeing directory (Shopify/Hydrogen storefront). She offers in-person sessions across Dubai, Sharjah, Ajman, and Umm Al Quwain: a free 20-minute consultation, a 60-minute session (AED 550), and a 90-minute extended session (AED 750), all booked through a 3-step widget that hands off to a real Shopify checkout. Audience: 7,785 IG followers (@lifecoach.ja), active with recent reels including a corporate session for Dubai's Department of Economy and Tourism (DET).
## Funnel Walk
Stop 1 (Entry — booking page): one clear next step ("Book a Session →"), narrows correctly — clean.
Stop 2 (Freebie): the only free step is the "Free Consultation - 20mins" option inside the booking widget itself, mislabeled "Price on request" instead of "Free" — folded into the Stop 3 finding below.
Stop 3 (Offer/pricing): the page hero and all 3 "You Might Also Like" expert cards on the same page show "Price on request / FROM" — but the booking widget one section below shows real, live AED 550 / AED 750 pricing. A visitor scanning for "what does this cost" in the first 10 seconds sees no price at all. Confirmed the same bug on the underlying raw Shopify product page ([theholisticculture.com/en-us/products/jamila-al-hosani](http://theholisticculture.com/en-us/products/jamila-al-hosani) — the #1 Google result for her name), which shows a static "AED 0.00" instead of resolving to the selected session's real price.
Stop 4 (Checkout/booking): manually click-walked the flow (session type → date → time). Real available dates surfaced (Jul 20-23, 27-30, Dubai time), real 5/6/7 PM time slots, hands off to "a secure Shopify checkout to complete payment" — functional, no leak here.
Stop 5 (Audience ownership): no email/list capture found anywhere in the crawled funnel — the 7,785 IG followers have no owned bridge; banked as #2 (mechanism, reframed as felt loss).
## Evidence
- Site vision pass: VISION PASS: COMPLETE — 3 of 3 required images confirmed read
- Pasted evidence: none attached (Notion page body was blank on intake)
- Machine flags rejected in the vision pass: 1 — "checkout blocked" ([packet.md](http://packet.md)'s Stop 4 read the embedded Shopify checkout as blocked-by-purchase; a manual click-through of session-select → date → time confirmed it actually works and hands off cleanly to a real payment step — that's the expected boundary of an unauthenticated crawl, not a defect, so the flag is dead)
## Gates
Gate 0: Pass — UAE-based (Dubai/Sharjah/Ajman/UAQ in-person practice, confirmed pre-flight), funnel floor confirmed by the full crawl (real AED 550/750 booking flow that reaches a live Shopify checkout), 30-day activity (recent IG reels incl. the Dubai DET corporate session), audience 7,785 (confirmed pre-flight).
Gate 1: Pass — solo practitioner, own face and bio, no named team or marketing lead. "Once your booking is confirmed, our team will contact you to coordinate the details" refers to the directory's own logistics team confirming an in-person location, not a gatekeeper standing between Haytham and Jamila.
## Lane + Finding
Lane 1: OPEN — felt leak survives the sting test and vitamin filter.
Finding: the page's hero price tag and all three other experts' cards read "Price on request" while her own booking widget, one section down on the same page, already shows live, bookable AED 550 / AED 750 pricing — real visitors are seeing a "you'll have to ask" signal at the exact moment they're deciding whether to keep going.
Innocent explanation: the directory platform's "From" price template field isn't wired to the real per-session pricing — the identical "Price on request" placeholder shows on all three other experts' cards on the same page, so this reads as a platform-wide display default, not anything Jamila configured or would necessarily know to check.
## Findings Bank
1. Hero price tag + all 3 "You Might Also Like" expert cards say "Price on request" while the booking widget one section below shows live AED 550/750 pricing — visitors scanning for price up top see nothing bookable. — innocent: the directory's "From" price template field likely isn't wired to real session pricing; identical placeholder repeats across every other expert's card on the same page, so it's a platform default, not her doing.
2. 7,785 IG followers (@lifecoach.ja) with zero email/list capture anywhere in the funnel — if Instagram access changed tomorrow, there's no way to reach any of them directly. — innocent: a solo, in-person practice booked session-by-session through the directory naturally leans on the platform's own booking + WhatsApp community first; a personal email bridge for the IG audience may simply not have been prioritized yet.
## Loom Skeleton
- Show: the "Price on request / FROM" tag in the hero of [theholisticculture.com/experts/jamila-al-hosani](http://theholisticculture.com/experts/jamila-al-hosani), plus the identical tag on the three "You Might Also Like" expert cards on the same page — right next to the "Book a Session" widget already showing AED 550 / AED 750.
- Fix: swap the static "Price on request" hero/card label for the real starting price (e.g. "From AED 550"), pulled from the same session data already feeding the booking widget beneath it — a copy/template change on the directory's expert-card component, not a rebuild.
- Done state: a visitor sees a real starting price the instant the page loads, with zero scrolling required to answer "what does this cost."
## SMYKM Hook
SMYKM hook: writes leadership-development posts in Arabic almost daily on LinkedIn, each one closing with a "رسالة التمكين" (empowerment message) plus a short practical self-assessment tool; her post today argued that being the strongest technical performer doesn't prepare someone to lead, and closed that "leadership begins when others' success becomes part of your responsibility." — WORK — source: [https://www.linkedin.com/posts/dr-jamila-alhosany-181a6629b_activity-7484498021422993408-8lZj](https://www.linkedin.com/posts/dr-jamila-alhosany-181a6629b_activity-7484498021422993408-8lZj) (posted 2026-07-19, read in full this session)
## Email Thread Log
2026-07-25 — Touch #2 — Subject: "the best performer isn't the leader" — Sent
Hey Jamila
Still thinking about that price on request label sitting above your real numbers.
While I was in there I also noticed there's no way for any of your 7,785 followers to leave an email anywhere on the site, so the list only exists on a platform you don't own.
Want me to record a quick video on both? Easier to show than explain.
Haytham
Reply: No reply
Next: Awaiting reply. Bank #2 spent; Touch 3 (disambiguating question) next if she stays quiet.
## Price Discovery
