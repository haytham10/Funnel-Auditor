<!--
VERBATIM ARCHIVE — DO NOT EDIT
Source: Notion page 39c382c8-4585-818a-a531-dfca72e2380e
Fetched: 2026-07-25T13:41:16Z
This is the unparsed original. The structured copy lives in Airtable
(Touches / Leads). If a parse is ever wrong, this is the source of truth.
-->

## Overview
Sasha Quince, "Conscious Love Mentor" — life/relationship coach for women, based in Abu Dhabi (confirmed in her own copy: moved to Dubai in 2006, Abu Dhabi client testimonials, Abu Dhabi references in her podcast). Solo operator, Kajabi. Main offer is "Heal You, Heal Your Relationships", an 11-week application-gated course (payment plans quoted from \$200-\$299/mo in the FAQ). Secondary paid mini-offer "Fear To Freedom" (2 weeks to secure love). 21,416 Instagram followers (@sashaquincelovecoach) plus a weekly podcast, "Heal You, Heal Your Relationship" — 110 episodes, latest Jul 2, 2026.
## Funnel Walk
Stop 1 (Entry/Sales) — The site URL IS the sales page: a long, well-built page, full 11-module curriculum, bonuses, real named UAE testimonials (Dubai 2024/2025, Abu Dhabi 2025), founder letter. No nav, no footer links — a standalone landing page whose only forward path is the Typeform. Nothing broken.
Stop 3 (Offer) — Price never appears on the page; it sits inside collapsed FAQ accordions ("How much is...", "Do you offer payment plans?"). Deliberate for an application funnel, not a leak.
Stop 4 (Checkout/Application) — The "APPLY HERE" Typeform (`/to/HqmmQEwp`) is LIVE and renders correctly on both desktop and mobile. The application handoff — the most likely place to find a leak — is healthy.
Stop 5 (Audience ownership) — Email capture DOES exist (the Fear To Freedom opt-in: first name, email, qualifying question, phone). Machine said "none anywhere"; that is wrong.
Distribution (podcast, off-site) — Where the leak actually lives. See Lane + Finding.
Orphan pages — `/store` renders "AVAILABLE PRODUCTS" over an empty shelf (two offer blocks resolve to nothing) with a "© 2026 Business Name" placeholder footer; `/sales-page` is an untouched Kajabi template ("\[ Offer Title \]", lorem ipsum, "Benefit 1/2/3"). Both are real but unlinked from her live funnel — weaker sting than the podcast link.
## Evidence
- Site vision pass: VISION PASS: COMPLETE — 8 of 8 required images confirmed read
- Pasted evidence: none — crawl-only walk (no images attached to the Notion page).
- Machine flags rejected in the vision pass: 3 — "Unavailable" (body copy: "attract Mr. Unavailable's your way", not an availability blocker); "no email capture anywhere" (false — the Fear To Freedom opt-in form renders fine); "\$4500/\$200/\$299 price mismatch" (not a mismatch — value-stack figure plus two payment-plan tiers for one product).
## Gates
Gate 0: Pass — UAE base confirmed (Abu Dhabi; her own copy + testimonials + podcast). Funnel exists (live sales page, live application, paid mini-offer). Activity: podcast episode Jul 2, 2026, 12 days ago, weekly cadence. Audience 21,416, well over the 1,500 floor.
Gate 1: Pass — solo operator. "I teach what I've lived", personal Gmail as the contact address, her own podcast, no team or gatekeeper anywhere on the site.
## Lane + Finding
Lane 1: Felt leak — a dead capture link on her single biggest live distribution channel.
Finding: The quiz link in her podcast show notes is typo'd — `pw556n5gt0l.typeform.com/to/lqsEV0Qvvv` (trailing `vvv`). It does not 404; Typeform silently redirects it to `typeform.com/explore`, Typeform's own marketing page ("You've taken one. Now make one. Get started — it's free"). Her listener gets pitched Typeform instead of her quiz. The correct ID is `lqsEV0Qv`, which returns HTTP 200 on her own account — the quiz exists and works. In her live Acast RSS feed the broken URL appears 406 times across 103 of 110 episodes, including the latest (Jul 2, 2026); the correct one appears twice. Confirmed visually (screenshot of the Typeform marketing page the link lands on) and independently by curl, which returns the redirect with Typeform's own `utm_content=typeform-incorrectURL` parameter.
Innocent explanation: she typed it right the first two times, then the show-notes template with the one-character typo got copy-pasted forward into every episode since — nobody clicks their own links.
## SMYKM Hook
SMYKM hook: On episode 106 she said the four things that held her 17-year partnership together were not what anyone expects, starting with it not being her partner's job to make her happy — WORK — source: [https://shows.acast.com/heal-you-heal-your-relationship/episodes/17-years-later-the-4-game-changers-that-built-secure-love](https://shows.acast.com/heal-you-heal-your-relationship/episodes/17-years-later-the-4-game-changers-that-built-secure-love)
## Email Thread Log
\[2026-07-15\] — Touch #1 — Subject: "episode 106" — Sent
Hey Sasha
Seventeen years, and the first thing on the list is that it was never his job to make you happy. Most people teaching relationships would not open there, because it does not flatter the listener.
The quiz you send people to at the end of the episodes has a typo in the link. Three extra letters on the end. It does not error, it quietly lands them on Typeform's own homepage, the one selling Typeform.
It is in 103 of your 110 episodes, including the one from July 2nd. So a woman finishes an episode and goes looking for the quiz. She gets an ad for a form builder.
Is that something you can swap out, or has it been copied forward too many times to chase?
Haytham
Reply: No reply
Next: 2026-07-18 — cold Touch 2 due
\[2026-07-18\] — Touch #2 — Subject: "episode 106" — Sent (Inbox 1)
Hey Sasha
The quiz link is the easy fix, once it's swapped it's swapped across all of them.
The reason I'd still record something is there's a bit more between someone finishing an episode and actually landing where you want them. Easier to show than explain. Want me to walk you through it, a few minutes, nothing to sit through live? You watch it on your own time.
Haytham
Reply: No reply
## Price Discovery
## Email Thread Log
2026-07-15 — Touch #1 — Subject: "episode 106" — Sent (scheduled 09:00 Gulf, drafted + scheduled 2026-07-14)
Hey Sasha
Seventeen years, and the first thing on the list is that it was never his job to make you happy. Most people teaching relationships would not open there, because it does not flatter the listener.
The quiz you send people to at the end of the episodes has a typo in the link. Three extra letters on the end. It does not error, it quietly lands them on Typeform's own homepage, the one selling Typeform.
It is in 103 of your 110 episodes, including the one from July 2nd. So a woman finishes an episode and goes looking for the quiz. She gets an ad for a form builder.
Is that something you can swap out, or has it been copied forward too many times to chase?
Haytham
Reply: No reply
Gate: CRM GATE (send): PASS — Sasha Quince: finding verified, email set, sends today 1/15
Next: 2026-07-18 — Touch 2 bump. Same subject, same thread. Bump the SAME finding (no new diagnosis, free-value cap).
