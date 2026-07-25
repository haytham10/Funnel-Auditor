# Bonge Gumede

<!-- airtable-record: TBD -->
> **Site:** https://officialbongegumede.com/ · **Profile:** https://www.instagram.com/bonge.gumede/
> **Walked:** 2026-07-17 · **Slug:** `bonge-gumede`

---

## Overview

Bonge Gumede — Dubai-based solo fitness coach ("Coach Bonge"). Runs a Shopify store (officialbongegumede.com) selling four digital fat-loss/muscle-building programs ($40-55, marked down from $80-100), a recurring "Building Capable Bodies" group challenge sold through Solin ($30, currently Group 2, kickoff July 20 2026), and a separate 1:1 "Apply Pressure" application funnel on its own domain. 64,100 IG followers (LinkedIn cites 350K+ combined across platforms). Challenge model has been running "almost 3 years" per its own sales page.

## Funnel Walk

- Stop 1 (Bio/Home) — officialbongegumede.com hero has one clear primary CTA ("SECURE YOUR SPOT HERE") for the live July challenge; nav also branches to Shop / 1:1 Coaching / Bio — no real ambiguity once past the hero (a machine flag of "5 near-equal links" as ambiguous was rejected on visual read).
- Stop 2 (Freebie) — No dedicated lead-magnet page. Footer newsletter opt-in ("JOIN 600+ SUBSCRIBERS") mentions a "complimentary gift" attached to the first email, but it has no landing page of its own — weak signal, not banked (mechanism, not a felt cost).
- Stop 3 (Offer/Sales) — Four Shopify digital programs ($40-$55) plus the July 20 Solin challenge cohort ($30) plus the separate Apply Pressure 1:1 application funnel.
- Stop 4 (Checkout) — Native Shopify cart on the main site; Solin external checkout reached, "Buy Now $30" / "Get Challenge Access" buttons visible and functional-looking (a machine flag of "blocked: no payment form" was rejected — that's a modal render a static crawl can't open, not a real break).
- Stop 5 (Audience Ownership) — Flodesk email capture present sitewide; not solely dependent on rented IG reach.

## Evidence

- **Site vision pass:** `VISION PASS: COMPLETE — 16 of 16 required images confirmed read`
- **Pasted evidence:** none — crawl-only walk (no images attached to the page).
- **Screenshots:** none promoted yet — see per-finding notes below

## Gates

- **Gate 0:** Pass — UAE-based (Dubai, confirmed at qualifying/pre-flight), funnel floor confirmed by the full crawl (live Shopify store, $40-100 programs, checkout reachable), audience 64,100 (IG), 30-day activity confirmed (July 20 cohort actively selling right now).
- **Gate 1:** Pass — solo personal brand throughout the funnel (own face, own story, "Coach Bonge"), no team/agency language on-site. (Settled at pre-flight; not re-litigated at the walk.)
- **Lane:** Lane 1 (felt leak) — a visually-confirmed finding survives both filters on a clearly committed, active-launch operator.

## Findings — reasoning

**Rank 1 — Sitewide banner advertises a two-month-stale challenge date**
Depth: not specified in raw archive · Type: stale content on every page
Innocent explanation: the announcement bar lives in Shopify's own theme settings, edited completely separately from the challenge listing hosted on Solin — an easy thing to let go stale when running back-to-back monthly cohorts on two different platforms.
Why it matters: the sitewide top banner reads "2026 MAY BUILDING CAPABLE BODIES CHALLENGE — REGISTER NOW" on every single page (home, every product page, the Shop collection page), while the challenge she's actually selling right now (via the Solin checkout) is the July 20 Group 2 kickoff — two months stale, on the one piece of chrome every visitor sees first.
Loom / fix path: show the green announcement bar at the very top of officialbongegumede.com — visible on the homepage and every product page — reading "2026 MAY BUILDING CAPABLE BODIES CHALLENGE - REGISTER NOW." Fix: in Shopify admin → Online Store → Theme → Announcement bar, update the text to reference the current cohort (July 20 Group 2, per the live Solin checkout) instead of May. Done state: a visitor landing from an IG link or a shared product page sees a banner that matches the challenge actually running right now, instead of a two-month-stale date.
Ruled out in the vision pass: three machine flags were rejected — "ambiguous bio entry" (the hero has one clear CTA, visually confirmed), "checkout blocked" (buy buttons render fine, only the payment modal is JS-gated), and "typeform quiz buttons no visible change" (expected behavior for a multi-step goal-selector, layout intact on screen).

**Rank 2 — Leftover Shopify demo product in the related-items carousel**
Depth: not specified in raw archive · Type: leftover placeholder content
Innocent explanation: default demo products ship unlisted and only surface in auto-populated related-product rows; it never shows in the main Shop grid, so it's an easy one to miss.
Why it matters: a leftover Shopify demo product ("Product title", generic clip-art t-shirt/notebook images, $19.99) appears in the "You might also like" carousel on all four course product pages — a stray, unbranded item sitting next to her real programs.
Evidence: none promoted yet

## SMYKM Hook

`her whole point of view that fitness is for being physically useful and ready for every good work, expanding a woman's capacity to serve rather than to attain a look or perfect the self — she reframes it for women moving away from influencer-driven fitness. Verified current, not just bio copy: her June 29 2026 post "5 reasons we train" lays out this exact framework in her own words.` — **WORK** — source: https://www.instagram.com/p/DaLb0b_hGEe/ (fetched via no-login Apify ig pull this session; corroborated by her July 5 2026 sabbatical-return post https://www.instagram.com/p/Daaz5JEF7pG/)

---

*Email history lives in Airtable (`Touches` table) — every send and reply, verbatim.
Price discovery answer and anchor live on the Airtable `Leads` record.
Neither is duplicated here.*
