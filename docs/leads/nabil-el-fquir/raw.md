<!--
VERBATIM ARCHIVE — DO NOT EDIT
Source: Notion page 3a0382c8-4585-816a-b960-e97083bceea8
Fetched: 2026-07-25T13:40:53Z
This is the unparsed original. The structured copy lives in Airtable
(Touches / Leads). If a parse is ever wrong, this is the source of truth.
-->

## Overview
Nabil El Fquir runs Job Search Mastery ([jobsearchmastery.me](http://jobsearchmastery.me)), a solo executive/career advisory for senior professionals (Managers, Directors, VPs) targeting UAE & GCC roles. Based in the UAE (Sharjah, Shams Media City); WordPress + WooCommerce, Stripe/Apple Pay/Tabby checkout, [cal.com](http://cal.com) booking. Paid ladder: CV & LinkedIn Optimisation (AED 2,899), Job Search Strategy Program (AED 3,799), Executive Interview Preparation (AED 4,999). Own face, first-person, active recruiter with 20+ years across MENA. LinkedIn audience 8,008. (No Cap LLC is his own operating entity / separate B2B recruitment arm — not a gatekeeper on this B2C advisory.)
## Funnel Walk
- Stop 1 (Entry / homepage) — Clean hero → single CTA ("Book a Strategy Call") + three package cards. Narrows well.
- Stop 2 (Freebie) — Four free resources (checklists/framework); each Download button routes to its own landing page WITH an email opt-in form (verified live). Captures contacts — not a leak.
- Stop 3 (Offer/Sales) — Three service cards, prices clear (AED 2,899 / 3,799 / 4,999), Tabby instalments shown. On the flagship AED 4,999 "Executive Interview Preparation" card, the "VIEW DETAILS" link points to /offer-conversion-advisory/ which is a hard 404. The other two cards' VIEW DETAILS resolve fine; the real detail page for this package lives at /executive-interview-preparation/.
- Stop 4 (Checkout/Booking) — WooCommerce checkout works (billing, Country=UAE, Stripe/Apple Pay/Tabby, VAT 5%). [cal.com](http://cal.com) booking calendar live with real slots (e.g. Mon 20 Jul: 12:15/1:00/1:45pm). No leak.
- Stop 5 (Audience ownership) — Email capture present on freebie landing pages; owns a list mechanism plus LinkedIn (8,008). Not fully rented. No leak.
## Evidence
- Site vision pass: VISION PASS: COMPLETE — 17 of 17 required images confirmed read
- Pasted evidence: none — crawl-only walk (Playwright fallback; Firecrawl MCP was unavailable at walk time).
- Machine flags rejected in the vision pass: 2 — freebie "no email capture" (opt-in form confirmed on each resource page); cart broken-image thumbnails (unset/lazy-load WooCommerce thumbnails, low felt cost).
- Independent verification: VERIFIED — AED 4,999 Executive Interview Preparation card VIEW DETAILS → /offer-conversion-advisory/ (live 404) vs working /executive-interview-preparation/ (live 200) confirmed on homepage HTML link mapping + curl HEAD/GET of both URLs.
## Gates
Gate 0: Pass — UAE-based confirmed (About: "Executive Career Coach in the UAE", Sharjah/Shams Media City); funnel/paid ladder live (AED 2,899-4,999); activity current (og:updated 2026-06-29 + active LinkedIn); audience 8,008 \> 1,500.
Gate 1: Pass — solo operator: own face, first-person copy, personal [cal.com](http://cal.com) booking, single-person About; No Cap LLC is his own entity, not a support/agency wall.
## Lane + Finding
- Lane 1 (Felt leak) — a broken detail path on the highest-ticket offer.
- Finding: The flagship AED 4,999 Executive Interview Preparation card's "VIEW DETAILS" link lands on a hard 404 ("This page doesn't seem to exist"), so a senior buyer who clicks to read the full page before committing to the most expensive package hits a dead end.
- Innocent explanation: the detail page was re-slugged (offer-conversion-advisory → executive-interview-preparation) and this one card's link was never repointed — a stale link from a rename, not a missing offer.
## Findings Bank
1. On the homepage offer section, the flagship AED 4,999 "Executive Interview Preparation" card's "VIEW DETAILS" link points to /offer-conversion-advisory/ and returns a hard 404, so the highest-intent senior buyer reading up on the most expensive package before paying lands on "This page doesn't seem to exist" — innocent: the page was renamed to /executive-interview-preparation/ and this card's link wasn't updated after the re-slug.
## Loom Skeleton
- Show: homepage advisory-packages section ([https://jobsearchmastery.me/](https://jobsearchmastery.me/)) — click "VIEW DETAILS" on the AED 4,999 Executive Interview Preparation card → [https://jobsearchmastery.me/offer-conversion-advisory/](https://jobsearchmastery.me/offer-conversion-advisory/) 404 page; then the working page at [https://jobsearchmastery.me/executive-interview-preparation/](https://jobsearchmastery.me/executive-interview-preparation/).
- Fix: repoint that card's "VIEW DETAILS" href from /offer-conversion-advisory/ to /executive-interview-preparation/ (WordPress: edit the card button link).
- Done state: clicking VIEW DETAILS on the AED 4,999 card opens its full sales page instead of a 404 — the top-tier buyer reads the detail and converts.
## SMYKM Hook
SMYKM hook: Your LinkedIn post this week reframing 'can you help me find a job?' into right person, right reason, clear relevance, reasonable ask — the cleanest breakdown of why senior networking messages get ignored that I've read. — WORK — source: [https://www.linkedin.com/posts/nabilelfquir_uaejobs-dubaijobs-hiring-activity-7483128480013086721-IJ8S](https://www.linkedin.com/posts/nabilelfquir_uaejobs-dubaijobs-hiring-activity-7483128480013086721-IJ8S)
## Email Thread Log
2026-07-25 — Touch #2 — Subject: "networking is not the ask" — Sent
Hey Nabil
Following up on that broken View Details link on your top package.
Want me to record a quick walkthrough of where it's pointed and what I'd fix? Easier to show than explain.
Haytham
Reply: No reply
Next: Awaiting reply. No second bank finding; Touch 3 (disambiguating question) next if she stays quiet.
## Price Discovery