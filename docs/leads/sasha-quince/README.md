# Sasha Quince

<!-- airtable-record: TBD -->
> **Site:** https://sasha-quince.mykajabi.com/HealYouHealYourRelationships · **Profile:** none found
> **Walked:** 2026-07-13 · **Slug:** `sasha-quince`

---

## Overview

Sasha Quince, "Conscious Love Mentor" — life/relationship coach for women, based in Abu Dhabi (confirmed in her own copy: moved to Dubai in 2006, Abu Dhabi client testimonials, Abu Dhabi references in her podcast). Solo operator, Kajabi. Main offer is "Heal You, Heal Your Relationships", an 11-week application-gated course (payment plans quoted from $200-$299/mo in the FAQ). Secondary paid mini-offer "Fear To Freedom" (2 weeks to secure love). 21,416 Instagram followers (@sashaquincelovecoach) plus a weekly podcast, "Heal You, Heal Your Relationship" — 110 episodes, latest Jul 2, 2026.

## Funnel Walk

- Stop 1 (Entry/Sales) — the site URL IS the sales page: a long, well-built page, full 11-module curriculum, bonuses, real named UAE testimonials (Dubai 2024/2025, Abu Dhabi 2025), founder letter. No nav, no footer links — a standalone landing page whose only forward path is the Typeform. Nothing broken.
- Stop 3 (Offer) — price never appears on the page; it sits inside collapsed FAQ accordions ("How much is...", "Do you offer payment plans?"). Deliberate for an application funnel, not a leak.
- Stop 4 (Checkout/Application) — the "APPLY HERE" Typeform (`/to/HqmmQEwp`) is LIVE and renders correctly on both desktop and mobile. The application handoff — the most likely place to find a leak — is healthy.
- Stop 5 (Audience ownership) — email capture DOES exist (the Fear To Freedom opt-in: first name, email, qualifying question, phone). Machine said "none anywhere"; that is wrong.
- Distribution (podcast, off-site) — where the leak actually lives. See Findings.
- Orphan pages — `/store` renders "AVAILABLE PRODUCTS" over an empty shelf (two offer blocks resolve to nothing) with a "© 2026 Business Name" placeholder footer; `/sales-page` is an untouched Kajabi template ("[ Offer Title ]", lorem ipsum, "Benefit 1/2/3"). Both are real but unlinked from her live funnel — weaker sting than the podcast link.

## Evidence

- **Site vision pass:** `VISION PASS: COMPLETE — 8 of 8 required images confirmed read`
- **Pasted evidence:** none — crawl-only walk (no images attached to the Notion page).
- **Screenshots:** none promoted yet — see per-finding notes below
- **Machine flags rejected in the vision pass:** 3 — "Unavailable" (body copy: "attract Mr. Unavailable's your way", not an availability blocker); "no email capture anywhere" (false — the Fear To Freedom opt-in form renders fine); "$4500/$200/$299 price mismatch" (not a mismatch — value-stack figure plus two payment-plan tiers for one product).

## Gates

- **Gate 0:** Pass — UAE base confirmed (Abu Dhabi; her own copy + testimonials + podcast). Funnel exists (live sales page, live application, paid mini-offer). Activity: podcast episode Jul 2, 2026, 12 days ago, weekly cadence. Audience 21,416, well over the 1,500 floor.
- **Gate 1:** Pass — solo operator. "I teach what I've lived", personal Gmail as the contact address, her own podcast, no team or gatekeeper anywhere on the site.
- **Lane:** Lane 1 (felt leak) — a dead capture link on her single biggest live distribution channel.

## Findings — reasoning

> The **canonical, structured** copy of each finding lives in Airtable (`Findings` table): rank, status, depth, type, innocent explanation, evidence path. This section carries the *reasoning* — why it's deep vs shallow, why it stings, what was ruled out. Don't duplicate the fields here; they will drift.
>
> No separate Findings Bank was recorded in the raw archive for this lead — only the one Lane 1 finding below was walked and verified.

**Rank 1 — typo'd quiz link in the podcast show notes silently redirects to Typeform's own marketing page**
Depth: DEEP · Type: Broken lead-capture link on the largest live distribution channel
Innocent explanation: she typed it right the first two times, then the show-notes template with the one-character typo got copy-pasted forward into every episode since — nobody clicks their own links.
Why it matters: the quiz link in her podcast show notes is typo'd — `pw556n5gt0l.typeform.com/to/lqsEV0Qvvv` (trailing "vvv"). It does not 404; Typeform silently redirects it to typeform.com/explore, Typeform's own marketing page ("You've taken one. Now make one. Get started — it's free"). Her listener gets pitched Typeform instead of her quiz. The correct ID is `lqsEV0Qv`, which returns HTTP 200 on her own account — the quiz exists and works. In her live Acast RSS feed the broken URL appears 406 times across 103 of 110 episodes, including the latest (Jul 2, 2026); the correct one appears twice. Confirmed visually (screenshot of the Typeform marketing page the link lands on) and independently by curl, which returns the redirect with Typeform's own `utm_content=typeform-incorrectURL` parameter.
Evidence: not yet promoted — see [`sasha-quince.raw.md`](./sasha-quince.raw.md) for citation.

## SMYKM Hook

SMYKM hook: On episode 106 she said the four things that held her 17-year partnership together were not what anyone expects, starting with it not being her partner's job to make her happy — WORK — source: [https://shows.acast.com/heal-you-heal-your-relationship/episodes/17-years-later-the-4-game-changers-that-built-secure-love](https://shows.acast.com/heal-you-heal-your-relationship/episodes/17-years-later-the-4-game-changers-that-built-secure-love)

---

*Email history lives in Airtable (`Touches` table) — every send and reply, verbatim.
Price discovery answer and anchor live on the Airtable `Leads` record.
Neither is duplicated here.*
