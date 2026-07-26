<!--
VERBATIM ARCHIVE — DO NOT EDIT
Source: Notion page 3a0382c8-4585-81c2-bfc6-f4e354a73096
Fetched: 2026-07-25T13:39:57Z
This is the unparsed original. The structured copy lives in Airtable
(Touches / Leads). If a parse is ever wrong, this is the source of truth.
-->

## Overview
Caroline Bakker (@amazonwarrior) — author, speaker, mindfulness meditation coach and holistic health advocate, based in Dubai. Runs a [stan.store](http://stan.store) link-in-bio storefront (platform: Other/Stan) selling a paid ladder: a free Nervous System Healing Kit opt-in, a \$7.99 ebook, several \$4.99 guided-meditation MP3s, a \$99 (from \$199) personalised meditation, plus an Amazon book and affiliate links. Second owned channel: YouTube "Meditations by Amazon Warrior" (5.57K). IG 8.2K. Also a branded site [carolinebakker.com](http://carolinebakker.com) and a 173-episode podcast.
## Funnel Walk
Stop 1 (Bio) — [stan.store](http://stan.store) storefront, own face + own story, \~15 product tiles. Solo personal brand, no gatekeeper.
Stop 2 (Freebie) — Free Nervous System Healing Kit, name+email opt-in form with SUBMIT & DOWNLOAD, visibly present and rendering (refutes the machine "no email capture" flag).
Stop 3 (Offer) — Personalised Meditation / Activation / Journey \$99 (from \$199), 5.0 rating; plus \$4.99 MP3s and \$7.99 ebook. Real paid ladder, visible pricing.
Stop 4 (Checkout) — [stan.store](http://stan.store) checkout is an in-SPA overlay; not separately crawlable (Playwright click-discovery also returned 0 navigable product URLs). Not a defect, a platform limitation.
Stop 5 (Audience ownership) — owned list capture DOES exist via the free-kit opt-in; not fully rented.
## Evidence
- Site vision pass: VISION PASS: COMPLETE — 2 of 2 required images confirmed read
- Pasted evidence: none — crawl-only walk (Firecrawl primary; Playwright `main.py walk` fallback used because [stan.store](http://stan.store) products are JS click-tiles with no anchor-discoverable URLs — the documented bio-link-aggregator fallback condition).
- Machine flags rejected in the vision pass: 3 — (1) "no email capture / fully rented" (freebie opt-in form is visibly present), (2) "Select a Provice/State" typo (Stan platform-default address dropdown, hidden select, not her editable copy, not on the storefront), (3) 20 "Edit Title/Edit Button Text" JS tokens (invisible DOM admin labels, not visible copy).
- Finding evidence path: evidence/caroline-bakker/screenshots/stan_store_amazonwarrior_desktop.png (and _mobile.png); text: evidence/caroline-bakker/pages/1_stan-store-amazonwarrior.txt lines 375-383.
- Independent verification: VERIFIED — "Being The Journey" buy button on Past Life Regression Meditation (\$4.99) confirmed on stan_store_amazonwarrior_desktop.png, _mobile.png, page text lines 380-383, and a fresh live Firecrawl re-fetch of [https://stan.store/amazonwarrior](https://stan.store/amazonwarrior) (DOM string, siblings "Get It Now"/"Relax Deeply"/"Listen Daily"). Held at Qualifying — email unverified.
## Gates
Gate 0: Pass — UAE base Dubai (confirmed; press release "Dubai Author Caroline Bakker"); funnel = real paid ladder w/ visible pricing; activity recent; audience 8.2K IG / 5.57K YouTube (both above 1,500 floor).
Gate 1: Pass — solo personal brand, own face + own story, own [stan.store](http://stan.store). No team/agency/gatekeeper.
## Lane + Finding
- Lane 1: Felt leak — a concrete, visible copy defect on a live paid-product buy button.
- Finding (bank #1): On the "Past Life Regression Meditation" product (\$4.99, from \$9.99), the buy button reads "Being The Journey" — a broken-looking call to action at the exact click-to-buy moment, and the only non-imperative among sibling buttons ("Get It Now", "Relax Deeply", "Listen Daily").
- Innocent explanation: almost certainly a typo of "Begin The Journey" made when setting the button text in Stan's editor — invisible to her because she reads it as intended.
## Findings Bank
1. "Being The Journey" typo on the Past Life Regression Meditation (\$4.99) buy button — reads broken where "Begin The Journey" was meant, on a live paid product — innocent: a one-word button-text typo in the Stan editor, easy to miss on your own page.
## Loom Skeleton
- Show: the "Past Life Regression Meditation" card on [https://stan.store/amazonwarrior](https://stan.store/amazonwarrior) — the peach "Being The Journey" button.
- Fix: in Stan, edit that product's button text from "Being The Journey" to "Begin The Journey" (an action phrase matching the neighbouring buttons).
- Done state: the buy button reads as a clear call to action, in line with "Get It Now" / "Relax Deeply" / "Listen Daily" on the surrounding cards.
## SMYKM Hook
SMYKM hook: Her book "The Healing Journey: Navigating Adult ADHD and PMDD" came straight out of her own story — self-diagnosing ADHD at 35, realizing how it amplified her PMDD into a "perfect storm", then building the holistic healing path she now teaches. — WORK — source: [https://www.goodreads.com/en/book/show/223237586-the-healing-journey](https://www.goodreads.com/en/book/show/223237586-the-healing-journey)
## Email Thread Log
2026-07-25 — Touch #2 — Subject: "the healing journey" — Sent
Hey Caroline
Circling back on that buy button that reads Being The Journey instead of Begin.
Want me to put together a short video on that button and what I'd change? Quicker to show than explain.
Haytham
Reply: No reply
Next: Awaiting reply. No second bank finding; Touch 3 (disambiguating question) next if she stays quiet.
## Price Discovery
