<!--
VERBATIM ARCHIVE — DO NOT EDIT
Source: Notion page 39e382c8-4585-8108-bb9e-d7b8f3d5d397
Fetched: 2026-07-25T13:41:16Z
This is the unparsed original. The structured copy lives in Airtable
(Touches / Leads). If a parse is ever wrong, this is the source of truth.
-->

## Overview
Salma El Shurafa — solo life/mindset/leadership coach and facilitator based in Dubai (Algarhoud), operating under her own "Aliveness" brand on a custom WordPress site. Offers 1:1 coaching, a 4-month "Aliveness" group coaching program (AED 6,800, Tabby installments), and corporate/leadership workshops. Founder of The Pathway Project (est. 2013), press-featured in The National, Marie Claire, Entrepreneur, and Khaleej Times. Primary owned channel is Instagram (@salma.elshurafa, 2,216 followers, active — posted within the last 2 weeks), plus an email list via on-page opt-ins.
## Funnel Walk
Stop 1 (Bio/Home) — homepage offers 3 near-equal paths (1:1, group coaching, free guidebook) with no single clear entry point; otherwise clean design.
Stop 2 (Freebie) — "7 Mindsets" guidebook opt-in is inline on the homepage (name/email fields) rather than a standalone landing page — present and functional, machine flag of "no freebie found" was a page-shape miss, not a broken flow.
Stop 3 (Offer/Sales) — /work-with-me (1:1 + corporate, no price shown) and /group-coaching (AED 6,800, Tabby 4x1,700) both live and on-brand.
Stop 4 (Checkout) — embedded directly on the group-coaching page (no separate checkout URL). The enrollment copy reads "Secure your spot before April 30th — only 10 spots are available" — that date has already passed as of this walk (2026-07-16). See Lane + Finding.
Stop 5 (Audience Ownership) — owns an email list (homepage + footer opt-in forms); Instagram is the largest channel (2,216 followers, verified) but its own feed embed fails to render anywhere it's placed on the site.
## Evidence
- Site vision pass: VISION PASS: COMPLETE — 8 of 8 required images confirmed read
- Pasted evidence: none — crawl-only walk
- Machine flags rejected in the vision pass: 1 — "unverified JS-only buttons" on /work-with-me and /group-coaching flagged by the crawl were confirmed on-screenshot as ordinary testimonial-carousel arrows, not a leak (obvious chrome).
## Gates
Gate 0: Pass — UAE-based (Dubai office address on the Contact page: Saleh Bin Lahej Building, Algarhoud; confirmed independently via LinkedIn and Crunchbase location); funnel present (two live sales pages + embedded Tabby checkout); activity floor met (Instagram post dated 2026-07-06, 10 days before this walk, geotagged Dubai); audience floor met (2,216 Instagram followers, verified via one Apify `ig --mode details` lookup — this corrects the intake note's "8-12k likes," which real per-post engagement does not support: likes run 22-121/post across the last 12 posts, with one clip at \~11,686 video views, not likes).
Gate 1: Pass — solo brand throughout, first-person copy on every page, no team/agency/gatekeeper language found.
## Lane + Finding
Lane 1: Felt leak — a stale, already-passed enrollment deadline sitting live on the paid checkout page.
Strongest finding: the AED 6,800 group-coaching page still tells visitors to "Secure your spot before April 30th — only 10 spots are available," a deadline that has already passed, on the exact page that takes payment via Tabby.
Innocent explanation: the page likely still carries copy from a past cohort launch that was never refreshed for the current round.
## Findings Bank
1. The AED 6,800 group-coaching checkout page runs a "secure your spot before April 30th" scarcity deadline that has already passed — anyone reading it now sees a paid program that looks unmaintained at the exact moment they're deciding to pay — innocent: evergreen sales page copy never updated after the last cohort launch.
2. The "Join My Movement" Instagram feed embed — her main proof of an active audience — never renders on any page it appears on (home, work-with-me, group-coaching, contact), showing only spinner icons where posts should be — innocent: the widget's embed token or connection likely expired rather than being removed on purpose.
## Loom Skeleton
- Show: [https://salmaelshurafa.com/group-coaching](https://salmaelshurafa.com/group-coaching) — the "Join the Journey: Awaken Your Aliveness" pricing block ("Secure your spot before April 30th").
- Fix: Swap the enrollment-deadline text and confirm the next cohort's real start date in that WordPress content block — a copy edit, no rebuild needed.
- Done state: The page shows a live, current enrollment window that matches the real next cohort, so the scarcity claim reads as true instead of stale.
## SMYKM Hook
SMYKM hook: she just announced bringing the complete Somatic Experiencing(R) Professional Training to the UAE for the first time — a 3-year body-based trauma-work program, Introductory cohort starting Sept or Dec — WORK — source: [https://www.instagram.com/p/DacC383M95Y/](https://www.instagram.com/p/DacC383M95Y/) (Jul 6, 2026, IG @salma.elshurafa)
## Email Thread Log
\[2026-07-18\] — Touch #1 — Subject: "bringing it to the uae" — Sent (Inbox 2)
Hey Salma
Somatic Experiencing has never run a full training in the UAE, and you are the one bringing it here this year. Three years of body based trauma work, first intro cohort this September or December.
What actually made me write though is I went through your Aliveness group coaching page after that.
The enrollment section still tells people to secure their spot before April 30th. That date's long gone.
A woman who reads the whole page, ready to pay 6,800 AED, hits that line right before she commits.
Is that just old copy sitting there, or is enrollment actually closed right now?
Haytham
\[2026-07-21\] — Touch #2 — Subject: "bringing it to the uae" (reply-in-thread) — Sent (Inbox 2)
Hey Salma
Another one from the same look around.
The Instagram feed embed under Join My Movement never actually loads anywhere it's placed, just a spinner icon in its spot.
\[carries bank #2, the dead IG embed finding\]
Reply: No reply yet
Next: 2026-07-27 — Touch 3 due, must carry the disambiguating question (bank spent)
## Price Discovery
