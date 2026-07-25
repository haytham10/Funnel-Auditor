<!--
VERBATIM ARCHIVE — DO NOT EDIT
Source: Notion page 3a2382c8-4585-8143-8918-f66fc890a464
Fetched: 2026-07-25T13:40:12Z
This is the unparsed original. The structured copy lives in Airtable
(Touches / Leads). If a parse is ever wrong, this is the source of truth.
-->

## Overview
Dr. Sheen Gurrib — solo content/podcast coach behind "The Dream Girl Podcast" and "The Podcast Academy," Dubai-based (Oxford/Cambridge grad, 861,458 IG followers, "Over 100M views," press-featured). Framer link-hub site funnelling to a Gumroad storefront: a tiered Podcast Masterclass ($99 per part / $275 full / $799 advanced-with-1:1) plus four PWYW digital products ($25 ChatGPT prompts, $45+ planner, $50 IG templates, $75+ bundle), and a standalone "BOOK A SESSION" 1:1 coaching CTA. Solo operator, own face/story throughout.
## Funnel Walk
Stop 1 (Entry — [sheengurrib.com](http://sheengurrib.com), Framer hub): About + press + "Digital Products" cards + "Book Sheen" section — all offers link out to Gumroad or Calendly.
Stop 2 (Course — The Podcast Academy, Gumroad qaprci): live, published, tiered $99/$275/$799, "Buy this" working — the anchor offer is healthy.
Stop 3 (Booking — Calendly "podcast-coaching-1-1-with-sheen"): renders "This Calendly URL is not valid." — the standalone paid 1:1 booking CTA dead-ends. LEAK.
Stop 4 (Digital products — Gumroad xwfba/pxrwxe/elbfi/xhmhb): all live with working checkouts; two landing-card prices overstate the live Gumroad price (Planner $65 on site vs $45+; Bundle $90 on site vs $75+). Minor LEAK.
Stop 5 (Capture/nurture): no email opt-in / lead magnet visible on the hub — everything routes straight to a paid Gumroad checkout. Noted, not the opener.
## Evidence
- Independent verification: VERIFIED. Homepage BOOK A SESSION 1:1 CTA dead-ends on Calendly 'This Calendly URL is not valid.' confirmed on evidence/dr-sheen-gurrib/screenshots/calendly_com_sheengurrib_podcast-coaching-1-1-with-sheen_desktop.png and _firecrawl_raw/calendly.html, plus an independent live Firecrawl re-render today (cacheState miss, US proxy). CTA-to-slug chain confirmed in _firecrawl_raw/1.html (single anchor to podcast-coaching-1-1-with-sheen, adjacent to the 699 price). Held at Qualifying: email unverified.
- Site vision pass: VISION PASS: COMPLETE — 8 of 8 required images confirmed read.
- Pasted evidence: none — crawl-only walk (Firecrawl primary + one Playwright cta-probe on the booking page).
- Machine flags rejected in the vision pass: 1 — the packet's "no cross-page mismatch" reconciliation was overruled (Planner/Bundle site-vs-Gumroad price gap confirmed by eye).
- Finding #1 rests on: evidence/dr-sheen-gurrib/screenshots/calendly_com_sheengurrib_podcast-coaching-1-1-with-sheen_desktop.png (renders "This Calendly URL is not valid."), evidence/dr-sheen-gurrib/screenshots/www_sheengurrib_com_desktop.png (the "Book Sheen" / BOOK A SESSION CTA on the hub), evidence/dr-sheen-gurrib/_firecrawl_raw/1.html (entry HTML carrying the calendly link + $699 price), and evidence/dr-sheen-gurrib/_firecrawl_raw/calendly.html. Independently reconfirmed by Playwright cta-probe (booking page yielded only a "Cookie settings" button, no slots) — this is a rendered-content finding, not a mobile-layout claim.
- Finding #2 rests on: evidence/dr-sheen-gurrib/screenshots/8936902398834_gumroad_com_l_xwfba_desktop.png (Planner $45+), evidence/dr-sheen-gurrib/screenshots/8936902398834_gumroad_com_l_xhmhb_desktop.png (Bundle $95 struck to $75+), vs the entry hub prices in evidence/dr-sheen-gurrib/screenshots/www_sheengurrib_com_desktop.png ($65 Planner / $90 Bundle) and [packet.md](http://packet.md).
## Gates
Gate 0: Pass — UAE base Dubai (confirmed pre-flight, apify IG details); funnel present (5 live Gumroad paid offers + course, confirmed by walk); activity within 30 days (posting daily 07-19); audience 861,458 IG.
Gate 1: Pass — solo operator; own face, own name, own story, first-person "I'm Sheen" throughout; no team/agency/support-desk language.
## Lane + Finding
Lane 1: Felt leak — a dead booking link on the highest-value standalone offer.
Finding: her homepage "BOOK A SESSION" 1:1 coaching CTA (a $699 offer) links to a Calendly page that returns "This Calendly URL is not valid." — anyone ready to book paid time with her hits a dead end and leaves.
Innocent explanation: the Calendly event type was likely renamed or unpublished and the site button still points at the old slug — a stale link, not a discontinued service (she still sells 1:1 time bundled into the $799 course tier).
## Findings Bank
1. The homepage "BOOK A SESSION" 1:1 coaching CTA ($699) dead-ends on a Calendly page reading "This Calendly URL is not valid." — the most expensive standalone offer is unbookable, so ready-to-buy attention is lost at the moment of purchase — innocent: the Calendly event was renamed/unpublished and the button still points at the old slug.
2. Two storefront cards quote a higher price than the live Gumroad checkout (Planner shown $65 vs $45+ live; Bundle shown $90 vs $75+ live) — the shopfront overstates her own prices, adding sticker-shock before the click — innocent: she lowered/PWYW'd the Gumroad prices and hasn't refreshed the Framer landing cards.
## Loom Skeleton
- Show: [sheengurrib.com](http://sheengurrib.com) "Book Sheen" section → click BOOK A SESSION → the Calendly "This Calendly URL is not valid." screen (URL: [calendly.com/sheengurrib/podcast-coaching-1-1-with-sheen](http://calendly.com/sheengurrib/podcast-coaching-1-1-with-sheen)).
- Fix: in Calendly, re-publish (or rename back) the 1:1 coaching event type, then repoint the Framer button to the current event URL.
- Done state: clicking BOOK A SESSION opens a live Calendly with bookable slots instead of an error — paid 1:1 requests land instead of bouncing.
## SMYKM Hook
SMYKM hook: Saw you caught Atif Aslam again this week in Abu Dhabi — 7th concert, 3rd country now. That's real loyalty. — LIFE — source: [https://www.instagram.com/p/Da-QoShiPtb/](https://www.instagram.com/p/Da-QoShiPtb/)
## Email Thread Log
\[2026-07-21\] — Touch #1 — Subject: "the Atif Aslam show" — Sent
Cold opener sent via Inbox 1, opening on the SMYKM hook and the Lane 1 finding (bank #1) per the row's Notes.
Reply: No reply
Next: 2026-07-24 — cold Touch 2 due (must carry the next unused Findings Bank entry, the Loom offer, or a disambiguating question — never a bare bump)
## Price Discovery
