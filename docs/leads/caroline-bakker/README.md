# Caroline Bakker

<!-- airtable-record: TBD -->
> **Site:** https://stan.store/amazonwarrior · **Profile:** https://stan.store/amazonwarrior
> **Walked:** 2026-07-17 · **Slug:** `caroline-bakker`

---

## Overview

Caroline Bakker (@amazonwarrior) — author, speaker, mindfulness meditation coach and holistic health advocate, based in Dubai. Runs a stan.store link-in-bio storefront (platform: Other/Stan) selling a paid ladder: a free Nervous System Healing Kit opt-in, a $7.99 ebook, several $4.99 guided-meditation MP3s, a $99 (from $199) personalised meditation, plus an Amazon book and affiliate links. Second owned channel: YouTube "Meditations by Amazon Warrior" (5.57K). IG 8.2K. Also a branded site carolinebakker.com and a 173-episode podcast.

## Funnel Walk

- Stop 1 (Bio) — stan.store storefront, own face + own story, ~15 product tiles. Solo personal brand, no gatekeeper.
- Stop 2 (Freebie) — Free Nervous System Healing Kit, name+email opt-in form with SUBMIT & DOWNLOAD, visibly present and rendering (refutes a machine "no email capture" flag).
- Stop 3 (Offer) — Personalised Meditation / Activation / Journey $99 (from $199), 5.0 rating; plus $4.99 MP3s and $7.99 ebook. Real paid ladder, visible pricing.
- Stop 4 (Checkout) — stan.store checkout is an in-SPA overlay; not separately crawlable (Playwright click-discovery also returned 0 navigable product URLs). Not a defect, a platform limitation.
- Stop 5 (Audience ownership) — owned list capture DOES exist via the free-kit opt-in; not fully rented.

## Evidence

- **Site vision pass:** `VISION PASS: COMPLETE — 2 of 2 required images confirmed read`
- **Pasted evidence:** none — crawl-only walk (Firecrawl primary; Playwright `main.py walk` fallback used because stan.store products are JS click-tiles with no anchor-discoverable URLs — the documented bio-link-aggregator fallback condition).
- **Screenshots:** none promoted yet — see per-finding notes below

## Gates

- **Gate 0:** Pass — UAE base Dubai (confirmed; press release "Dubai Author Caroline Bakker"); funnel = real paid ladder w/ visible pricing; activity recent; audience 8.2K IG / 5.57K YouTube (both above 1,500 floor).
- **Gate 1:** Pass — solo personal brand, own face + own story, own stan.store. No team/agency/gatekeeper.
- **Lane:** Lane 1 (felt leak) — a concrete, visible copy defect on a live paid-product buy button.

## Findings — reasoning

**Rank 1 — Buy button reads as a typo at the click-to-buy moment**
Depth: not specified in raw archive · Type: broken/typo CTA copy
Innocent explanation: almost certainly a typo of "Begin The Journey" made when setting the button text in Stan's editor — invisible to her because she reads it as intended.
Why it matters: on the "Past Life Regression Meditation" product ($4.99, from $9.99), the buy button reads "Being The Journey" — a broken-looking call to action at the exact click-to-buy moment, and the only non-imperative among sibling buttons ("Get It Now", "Relax Deeply", "Listen Daily").
Loom / fix path: show the "Past Life Regression Meditation" card on https://stan.store/amazonwarrior — the peach "Being The Journey" button. Fix: in Stan, edit that product's button text from "Being The Journey" to "Begin The Journey" (an action phrase matching the neighbouring buttons). Done state: the buy button reads as a clear call to action, in line with "Get It Now" / "Relax Deeply" / "Listen Daily" on the surrounding cards.
Ruled out in the vision pass: three machine flags were rejected — (1) "no email capture / fully rented" (freebie opt-in form is visibly present), (2) "Select a Provice/State" typo (a Stan platform-default address dropdown, hidden select, not her editable copy, not on the storefront), (3) 20 "Edit Title/Edit Button Text" JS tokens (invisible DOM admin labels, not visible copy).
Independent verification: VERIFIED — "Being The Journey" buy button on Past Life Regression Meditation ($4.99) confirmed on desktop and mobile screenshots, page text, and a fresh live Firecrawl re-fetch of https://stan.store/amazonwarrior (DOM string, siblings "Get It Now"/"Relax Deeply"/"Listen Daily"). Held at Qualifying at the time of the walk — email unverified.
Evidence: none promoted yet

## SMYKM Hook

`Her book "The Healing Journey: Navigating Adult ADHD and PMDD" came straight out of her own story — self-diagnosing ADHD at 35, realizing how it amplified her PMDD into a "perfect storm", then building the holistic healing path she now teaches.` — **WORK** — source: https://www.goodreads.com/en/book/show/223237586-the-healing-journey

---

*Email history lives in Airtable (`Touches` table) — every send and reply, verbatim.
Price discovery answer and anchor live on the Airtable `Leads` record.
Neither is duplicated here.*
