# Salma El Shurafa

<!-- airtable-record: TBD -->
> **Site:** https://salmaelshurafa.com/ · **Profile:** https://www.instagram.com/salma.elshurafa/
> **Walked:** 2026-07-15 · **Slug:** `salma-el-shurafa`

---

## Overview

Salma El Shurafa — solo life/mindset/leadership coach and facilitator based in Dubai (Algarhoud), operating under her own "Aliveness" brand on a custom WordPress site. Offers 1:1 coaching, a 4-month "Aliveness" group coaching program (AED 6,800, Tabby installments), and corporate/leadership workshops. Founder of The Pathway Project (est. 2013), press-featured in The National, Marie Claire, Entrepreneur, and Khaleej Times. Primary owned channel is Instagram (@salma.elshurafa, 2,216 followers, active — posted within the last 2 weeks), plus an email list via on-page opt-ins.

## Funnel Walk

- Stop 1 (Bio/Home) — homepage offers 3 near-equal paths (1:1, group coaching, free guidebook) with no single clear entry point; otherwise clean design.
- Stop 2 (Freebie) — "7 Mindsets" guidebook opt-in is inline on the homepage (name/email fields) rather than a standalone landing page — present and functional, machine flag of "no freebie found" was a page-shape miss, not a broken flow.
- Stop 3 (Offer/Sales) — /work-with-me (1:1 + corporate, no price shown) and /group-coaching (AED 6,800, Tabby 4x1,700) both live and on-brand.
- Stop 4 (Checkout) — embedded directly on the group-coaching page (no separate checkout URL). The enrollment copy reads "Secure your spot before April 30th — only 10 spots are available" — that date has already passed as of this walk (2026-07-16). See Findings.
- Stop 5 (Audience Ownership) — owns an email list (homepage + footer opt-in forms); Instagram is the largest channel (2,216 followers, verified) but its own feed embed fails to render anywhere it's placed on the site.

## Evidence

- **Site vision pass:** `VISION PASS: COMPLETE — 8 of 8 required images confirmed read`
- **Pasted evidence:** none — crawl-only walk
- **Screenshots:** none promoted yet — see per-finding notes below
- **Machine flags rejected in the vision pass:** 1 — "unverified JS-only buttons" on /work-with-me and /group-coaching flagged by the crawl were confirmed on-screenshot as ordinary testimonial-carousel arrows, not a leak (obvious chrome).

## Gates

- **Gate 0:** Pass — UAE-based (Dubai office address on the Contact page: Saleh Bin Lahej Building, Algarhoud; confirmed independently via LinkedIn and Crunchbase location); funnel present (two live sales pages + embedded Tabby checkout); activity floor met (Instagram post dated 2026-07-06, 10 days before this walk, geotagged Dubai); audience floor met (2,216 Instagram followers, verified via one Apify `ig --mode details` lookup — this corrects the intake note's "8-12k likes," which real per-post engagement does not support: likes run 22-121/post across the last 12 posts, with one clip at ~11,686 video views, not likes).
- **Gate 1:** Pass — solo brand throughout, first-person copy on every page, no team/agency/gatekeeper language found.
- **Lane:** Lane 1 (felt leak) — a stale, already-passed enrollment deadline sitting live on the paid checkout page.

## Findings — reasoning

> The **canonical, structured** copy of each finding lives in Airtable (`Findings` table): rank, status, depth, type, innocent explanation, evidence path. This section carries the *reasoning* — why it's deep vs shallow, why it stings, what was ruled out. Don't duplicate the fields here; they will drift.

**Rank 1 — stale, already-passed enrollment deadline live on the paid checkout page**
Depth: DEEP · Type: Expired urgency copy on a paid checkout page
Innocent explanation: the page likely still carries copy from a past cohort launch that was never refreshed for the current round.
Why it matters: the AED 6,800 group-coaching page still tells visitors to "Secure your spot before April 30th — only 10 spots are available," a deadline that has already passed, on the exact page that takes payment via Tabby — anyone reading it now sees a paid program that looks unmaintained at the exact moment they're deciding to pay. Loom framing: show the "Join the Journey: Awaken Your Aliveness" pricing block on /group-coaching; the fix is a straight copy swap of the enrollment-deadline text for the real next-cohort date in the WordPress content block, no rebuild needed; done state is a live, current enrollment window that matches the real next cohort so the scarcity claim reads as true instead of stale.
Evidence: not yet promoted — see [`salma-el-shurafa.raw.md`](./salma-el-shurafa.raw.md) for citation.

**Rank 2 — "Join My Movement" Instagram feed embed never renders** *(RESERVED — call bait, never emailed)*
Depth: SHALLOW · Type: Broken social-proof embed
Innocent explanation: the widget's embed token or connection likely expired rather than being removed on purpose.
Why it matters: this is her main proof of an active audience, and it never renders on any page it appears on (home, work-with-me, group-coaching, contact) — only spinner icons where posts should be. A trust signal, not a money leak, so it rides behind Rank 1.
Evidence: not yet promoted — see [`salma-el-shurafa.raw.md`](./salma-el-shurafa.raw.md) for citation.

## SMYKM Hook

SMYKM hook: she just announced bringing the complete Somatic Experiencing(R) Professional Training to the UAE for the first time — a 3-year body-based trauma-work program, Introductory cohort starting Sept or Dec — WORK — source: [https://www.instagram.com/p/DacC383M95Y/](https://www.instagram.com/p/DacC383M95Y/) (Jul 6, 2026, IG @salma.elshurafa)

---

*Email history lives in Airtable (`Touches` table) — every send and reply, verbatim.
Price discovery answer and anchor live on the Airtable `Leads` record.
Neither is duplicated here.*
