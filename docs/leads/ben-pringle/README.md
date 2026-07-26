# Ben Pringle

<!-- airtable-record: TBD -->
> **Site:** https://stan.store/uaefootballnetwork · **Profile:** https://ae.linkedin.com/in/ben-pringle-9663aa18b
> **Walked:** 2026-07-13 · **Slug:** `ben-pringle`

---

## Overview

Ben Pringle — ex-EFL professional footballer, now Head Coach at Precision Football Club in Dubai and founder of UAE Football Network. Fitness/sports coach, Dubai, selling off a Stan.store bio-link page (Platform: Other). One priced product now live: a 1-to-1 Call with Ben Pringle (£50, "Contract and signing call with Head Coach of Precision Football Club"). A second product, The Dubai Football Guide (£40, marked down from £99, 5.0 rated), was live at the original walk (2026-07-13) and is gone from the store entirely as of a re-walk on 2026-07-18 — see Findings. His flagship push is "UAE Football Network Pre Season Dubai 2026" — an application form for players wanting training, club options and introductions in the UAE. Audience 9,057 on Instagram (@uaefootballnetwork, 194 posts), posting near-daily. Gulf News have covered him ("Ben Pringle on swapping the EFL for UAE football").

## Funnel Walk

- Stop 1 (Bio) — Stan.store page, live, renders clean on desktop and mobile; IG bio link points here (confirmed via read-only profile pull) — the front door works.
- Stop 2 (Freebie) — no true freebie. The Pre Season 2026 form is an application, not a lead magnet. Its button reads "SUBMIT & DOWNLOAD" against copy above it that says "Fill out the form below and we'll be in touch," a label mismatch, but a live test submission (2026-07-18, Haytham) confirmed the form shows an on-page confirmation modal after submit ("You're in! I'll be in touch with you soon."). Applicants are told it landed. This no longer clears the felt-cost bar — demoted, not the finding.
- Stop 3 (Offer/Sales) — one product now: the £50 1:1 call, priced and live on the bio page itself. No separate sales page; Stan renders it inline. The £40 Dubai Football Guide card, live and 5.0-rated at the original walk, is gone entirely from the page as of the re-walk — no card, no sold-out notice, nothing. See Findings.
- Stop 4 (Checkout) — Stan's standard in-modal checkout; not reachable by a stateless crawl. Machine flagged "no checkout reached" — rejected, the remaining product card and buy CTA render fine.
- Stop 5 (Audience Ownership) — the Pre Season form captures name, email, phone, country, CV/Transfermarkt link and Instagram. So a list is being built through that form; the confirmation modal means the funnel step itself works as intended.

## Evidence

- **Site vision pass (original walk, 2026-07-13):** `VISION PASS: COMPLETE — 2 of 2 required images confirmed read (desktop + mobile of the Stan store, pre-submission state).`
- **Pasted evidence:** none — crawl-only walk both times.
- **Screenshots:** none promoted yet — see per-finding notes below. A re-walk on 2026-07-18 re-captured the store with a fresh Firecrawl capture (proxy: stealth) — desktop viewport, full-page, and mobile all read in full; the full-page screenshot is byte-identical to the viewport capture, confirming no additional content below the fold; the Dubai Football Guide product card is absent from all three captures and from the scraped markdown text. 3 machine flags rejected in the original vision pass: price-mismatch (£40/£99 is deliberate strikethrough framing, not an inconsistency); JS-buttons-unverified (both product CTAs render fine; unverified ≠ broken); no-checkout-reached (crawl limitation, Stan modal, not a dead checkout). Note on fetch: a direct Firecrawl scrape of Stan.store bounced to Stan's marketing homepage during the original qualifying pass (bot wall); both walks got through with proxy: stealth, and the original walk was also re-run through the Playwright fallback (`main.py walk`) for click-discovery — all paths rendered his real store (title: "UAE Football Network (@uaefootballnetwork) | Stan", HTTP 200).
- **Re-walk 2026-07-25** (evidence-persistence migration, proxy: stealth): the store now shows **two** products again — "1-to-1 Call with Ben Pringle" (£50) AND "The Dubai Football Guide" (£40, struck through £99, 5.0 rating, "LEARN MORE" button), both confirmed in the scraped markdown and visually on a fresh full-page screenshot. The Rank 1 finding (vanished product) is **no longer true as of today**. Raw capture (not promoted — it disproves the finding rather than confirming it, so there is nothing to bank): [../../evidence/ben-pringle/screenshots/store_rewalk_20260725.png](../../evidence/ben-pringle/screenshots/store_rewalk_20260725.png).

## Gates

- **Gate 0:** Pass — UAE base confirmed (LinkedIn: Head Coach at Precision Football Club in Dubai; IG bio "🇦🇪 | Dubai"; Gulf News Dubai coverage). Funnel floor: one live priced product (£50) plus the Pre Season application funnel. Activity floor: last Instagram post 2026-07-13, posting near-daily; recent LinkedIn post "2 weeks to go — UAE Football Network Manchester". Audience floor: 9,057 IG, well over 1,500.
- **Gate 1:** Pass — solo operator. The store byline is "Ben Pringle: Founder | UEFA Licensed Coach | Professional Footballer", the IG bio reads "Owner - @benpringle18", and the paid product is literally a call with him. No agency, no gatekeeper, no team.
- **Lane:** Lane 1 (felt leak) — a live, rated revenue product has silently disappeared from the only storefront he has.

## Findings — reasoning

> The **canonical, structured** copy of each finding lives in Airtable (`Findings` table):
> rank, status, depth, type, innocent explanation, evidence path. This section carries the
> *reasoning* — why it's deep vs shallow, why it stings, what was ruled out. Don't duplicate
> the fields here; they will drift.

**Rank 1 — a live, 5.0-rated £40 product has disappeared entirely from the store**
Depth: DEEP · Type: vanished revenue product, no explanation left behind
Innocent explanation: could be a deliberate declutter, narrowing the store to the Pre Season push and the 1:1 call while the guide gets reworked, or it could have quietly unpublished itself, a Stan glitch, or gotten toggled off by accident while he was editing something else on the page.
Why it matters: the Dubai Football Guide — £40, marked down from £99, carrying a 5.0 rating — was live on this exact page as of the original walk (2026-07-13). As of the 2026-07-18 re-walk it is gone entirely: no product card, no "sold out" notice, no redirect, nothing marking that it ever existed. The store now shows a single product (the £50 1:1 call). Anyone who saw the guide before, or any past 5-star buyer who'd refer a friend to it, hits nothing where a real, working, rated product used to be. This was visually confirmed on fresh full-page + mobile screenshots taken specifically for the re-walk.
Re-walked 2026-07-25: **no longer present as of 2026-07-25** — original evidence lost (pre-persistence). The Dubai Football Guide is back on the store page (£40, struck through £99, 5.0 rating, "LEARN MORE" CTA) alongside the £50 1:1 call — two products live again, confirmed via fresh Firecrawl capture (proxy: stealth) and full-page screenshot. This finding is now DEAD — do not reference "the guide has disappeared" in any future outreach to this lead.
Evidence: none promoted (finding invalidated, not confirmed) — raw disproof capture at [../../evidence/ben-pringle/screenshots/store_rewalk_20260725.png](../../evidence/ben-pringle/screenshots/store_rewalk_20260725.png)

**Rank 2 — RETIRED, do not reuse — "SUBMIT & DOWNLOAD" button with no confirmation**
Depth: was SHALLOW · Type: button-label mismatch (invalidated as a leak)
Innocent explanation: n/a — invalidated, not a live issue.
Why it matters (historical, now closed): the original finding claimed the Pre Season application's "SUBMIT & DOWNLOAD" button promised a download and gave no confirmation, leaving applicants unsure whether it went through. Haytham test-submitted the live form on 2026-07-18 and received an on-page confirmation modal ("You're in! I'll be in touch with you soon."), which disproves the "no confirmation" claim. The button-label mismatch itself (promises a download, delivers a text message) is real but minor and was never the actual leak — do not reuse "no confirmation" or "left wondering whether it went through" in any future copy to this lead.
Evidence: none promoted yet

## SMYKM Hook

`He announced his retirement from playing on LinkedIn in June after 22 years, closing it "The best job in the world" — and three days later posted that he'd been named First Team Head Coach at Precision.` — **LIFE** — source: https://www.linkedin.com/posts/ben-pringle-9663aa18b_from-working-in-all-saints-and-playing-part-time-activity-7473415371220512768-HYWt

---

*Email history lives in Airtable (`Touches` table) — every send and reply, verbatim.
Price discovery answer and anchor live on the Airtable `Leads` record.
Neither is duplicated here.*
