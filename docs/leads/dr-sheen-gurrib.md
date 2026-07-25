# Dr. Sheen Gurrib

<!-- airtable-record: TBD -->
> **Site:** https://www.sheengurrib.com/ · **Profile:** https://www.instagram.com/sheengurrib
> **Walked:** 2026-07-19 · **Slug:** `dr-sheen-gurrib`

---

## Overview

Dr. Sheen Gurrib — solo content/podcast coach behind "The Dream Girl Podcast" and "The Podcast Academy,"
Dubai-based (Oxford/Cambridge grad, 861,458 IG followers, "Over 100M views," press-featured). Framer
link-hub site funnelling to a Gumroad storefront: a tiered Podcast Masterclass ($99 per part / $275 full /
$799 advanced-with-1:1) plus four PWYW digital products ($25 ChatGPT prompts, $45+ planner, $50 IG
templates, $75+ bundle), and a standalone "BOOK A SESSION" 1:1 coaching CTA. Solo operator, own
face/story throughout.

## Funnel Walk

- Stop 1 (Entry — sheengurrib.com, Framer hub) — About + press + "Digital Products" cards + "Book Sheen"
  section — all offers link out to Gumroad or Calendly.
- Stop 2 (Course — The Podcast Academy, Gumroad qaprci) — live, published, tiered $99/$275/$799, "Buy
  this" working — the anchor offer is healthy.
- Stop 3 (Booking — Calendly "podcast-coaching-1-1-with-sheen") — renders "This Calendly URL is not
  valid." — the standalone paid 1:1 booking CTA dead-ends. LEAK.
- Stop 4 (Digital products — Gumroad xwfba/pxrwxe/elbfi/xhmhb) — all live with working checkouts; two
  landing-card prices overstate the live Gumroad price (Planner $65 on site vs $45+; Bundle $90 on site
  vs $75+). Minor LEAK.
- Stop 5 (Capture/nurture) — no email opt-in / lead magnet visible on the hub — everything routes
  straight to a paid Gumroad checkout. Noted, not the opener.

## Evidence

- **Site vision pass:** `VISION PASS: COMPLETE — 8 of 8 required images confirmed read`
- **Pasted evidence:** none — crawl-only walk (Firecrawl primary + one Playwright cta-probe on the
  booking page). Machine flags rejected in the vision pass: 1 — the packet's "no cross-page mismatch"
  reconciliation was overruled (Planner/Bundle site-vs-Gumroad price gap confirmed by eye). Independent
  verification: VERIFIED — Homepage BOOK A SESSION 1:1 CTA dead-ends on Calendly "This Calendly URL is
  not valid." confirmed on evidence/dr-sheen-gurrib/screenshots/calendly_com_sheengurrib_podcast-
  coaching-1-1-with-sheen_desktop.png and _firecrawl_raw/calendly.html, plus an independent live
  Firecrawl re-render (cacheState miss, US proxy). CTA-to-slug chain confirmed in
  _firecrawl_raw/1.html (single anchor to podcast-coaching-1-1-with-sheen, adjacent to the 699 price).
  Held at Qualifying: email unverified.
- **Screenshots:** none promoted yet — see per-finding notes below

## Gates

- **Gate 0:** Pass — UAE base Dubai (confirmed pre-flight, apify IG details); funnel present (5 live
  Gumroad paid offers + course, confirmed by walk); activity within 30 days (posting daily 07-19);
  audience 861,458 IG.
- **Gate 1:** Pass — solo operator; own face, own name, own story, first-person "I'm Sheen" throughout;
  no team/agency/support-desk language.
- **Lane:** Lane 1 (felt leak) — a dead booking link on the highest-value standalone offer.

## Findings — reasoning

> The **canonical, structured** copy of each finding lives in Airtable (`Findings` table): rank, status,
> depth, type, innocent explanation, evidence path. This section carries the *reasoning* — why it's deep
> vs shallow, why it stings, what was ruled out. Don't duplicate the fields here; they will drift.

**Rank 1 — "BOOK A SESSION" ($699) dead-ends on an invalid Calendly link**
Depth: DEEP · Type: dead booking link on the highest-priced standalone offer
Innocent explanation: the Calendly event type was likely renamed or unpublished and the site button
still points at the old slug — a stale link, not a discontinued service (she still sells 1:1 time
bundled into the $799 course tier).
Why it matters: her homepage "BOOK A SESSION" 1:1 coaching CTA (a $699 offer) links to a Calendly page
that returns "This Calendly URL is not valid." — anyone ready to book paid time with her hits a dead end
and leaves; the most expensive standalone offer is unbookable, so ready-to-buy attention is lost at the
moment of purchase. Show/Fix/Done from the walk's Loom skeleton: Show sheengurrib.com "Book Sheen"
section → click BOOK A SESSION → the Calendly "This Calendly URL is not valid." screen (URL:
calendly.com/sheengurrib/podcast-coaching-1-1-with-sheen). Fix: in Calendly, re-publish (or rename back)
the 1:1 coaching event type, then repoint the Framer button to the current event URL. Done state:
clicking BOOK A SESSION opens a live Calendly with bookable slots instead of an error — paid 1:1 requests
land instead of bouncing.
Evidence: [`finding-1.png`](./evidence/finding-1.png) (not yet promoted)

**Rank 2 — Two storefront cards overstate their live Gumroad price** *(RESERVED — call bait, never emailed)*
Depth: SHALLOW · Type: price mismatch across pages
Innocent explanation: she lowered/PWYW'd the Gumroad prices and hasn't refreshed the Framer landing
cards.
Why it matters: Planner shown $65 on the hub vs $45+ live; Bundle shown $90 vs $75+ live — the shopfront
overstates her own prices, adding sticker-shock before the click.

## SMYKM Hook

`Saw you caught Atif Aslam again this week in Abu Dhabi — 7th concert, 3rd country now. That's real
loyalty.` — **LIFE** — source: https://www.instagram.com/p/Da-QoShiPtb/

---

*Email history lives in Airtable (`Touches` table) — every send and reply, verbatim.
Price discovery answer and anchor live on the Airtable `Leads` record.
Neither is duplicated here.*
