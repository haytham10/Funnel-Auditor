# William Brown

<!-- airtable-record: TBD -->
> **Site:** https://williambrown1.podia.com · **Profile:** https://www.linkedin.com/in/william-brown-01a310182
> **Walked:** 2026-07-16 · **Slug:** `william-brown`

---

## Overview

William Brown — Business/Leadership coach, dual-based Bali/Dubai with a confirmed Dubai operating base (Ritz Carlton JBR events, Palm Jumeirah content, ae.linkedin.com profile). Runs "William Brown Consulting Services" (branded "Build Grow & Exit" at checkout) on Podia: a £97 "How To: $10M Behind The Scenes" bonus course and the flagship £8,000 "The Dubai Boardroom Mastermind" (in-person, Ritz Carlton JBR, 27-29 Nov 2026). 57,928 verified Instagram followers (@willia_mbrown, business account), active (posted 28 days ago). Solo operator, no team/gatekeeper language anywhere.

This lead has a live/warm thread (status Reply Received as of this archive) and is slated for a re-walk in R6, so the Findings section below aims for high fidelity to the raw archive rather than a light summary.

## Funnel Walk

- Stop 1 (Entry — williambrown1.podia.com) — clean, two products listed with clear price/lesson count, one obvious next step each. No issue.
- Stop 2 (Freebie) — none found — everything routes straight to paid (£97 or £8,000). Email capture exists in the footer sign-up form, so audience ownership isn't zero. Vitamin-trap territory, not banked.
- Stop 3 (Offer/Sales — Dubai Boardroom Mastermind page) — the public, pre-purchase page renders the ENTIRE 148-lesson curriculum in full descriptions (not just titles) — real internal training content, downloadable file names, sales-call recordings by first name, and a live Mamopay payment link ("Here is the link to pay for the program and get access") for a completely different, unmarketed, undisclosed-price program ("Decisionary Coach Accelerator") sitting inside the lesson text. Any visitor can read the whole £8,000 program's content and even pay for a second product without ever buying the mastermind. Tier A — banked as finding #1.
- Stop 4 (Checkout — both offers) — functional, correct price, Cloudflare-verified, no errors. But both are bare stock Podia carts — no order bump, no guarantee, no social proof at the highest-intent moment. Tier B — banked as finding #2.
- Stop 5 (Audience ownership) — footer email capture exists; not fully rented. No issue banked.

## Evidence

- **Site vision pass:** `VISION PASS: COMPLETE — 9 of 9 required images confirmed read`
- **Pasted evidence:** none attached — crawl-only walk.
- **Screenshots:** none promoted yet — see per-finding notes below. 3 machine flags rejected in the vision pass: price-mismatch (marketing-copy revenue figures $16.4M/$42M misread as product price, actual price £8,000 confirmed identical on sales page + checkout via screenshot); harvested-email "picard@starfleet.org" (placeholder text in the checkout email input, not a real address, confirmed via screenshot); unverified JS-only checkout buttons "Continue/Edit/Pay now" ×2 pages (confirmed-benign — normal functioning checkout chrome, visually verified).
- **2026-07-25 re-walk:** Rank 1 re-checked live against the current site — **still present, no change.** Fresh Firecrawl scrape (markdown + full-page screenshot, no login) of the Dubai Boardroom Mastermind product page (current URL: `https://williambrown1.podia.com/6303f1c4-0eed-4567-8b6c-c8bf21216e84`) confirms the full 148-lesson curriculum still renders in full descriptions to a logged-out visitor, and the "Link To Download My 'Decisionary Coach Accelerator' Program [My Sales Rep Training Course]" lesson block still exposes the same live Mamopay payment link (`https://business.mamopay.com/pay/williambrownconsultingservices-b39ab8`) with the identical copy ("Here is the link to pay for the program and get access"). The full-page screenshot is 1920×17051px (page is very long); the promoted evidence file is a downscaled thumbnail (180×1600) and is not legible at the specific lesson-block text level — the markdown capture of that exact lesson block (quoted above and in the finding note below) is the stronger proof for this re-walk. See [./evidence/](./evidence/) for the promoted screenshot.

## Gates

- **Gate 0:** Pass — UAE-based (Dubai events + content, confirmed pre-flight), funnel confirmed (two live, working paid products with functioning checkout), activity floor met (IG post 28 days old, 2026-06-18), audience floor met (57,928 IG followers, hard number via Apify, well above 1,500).
- **Gate 1:** Pass — solo operator, first-person voice throughout, own verified IG/LinkedIn, no team or gatekeeper language anywhere in the funnel.
- **Lane:** Lane 1 (felt leak) — on a committed, real, active buyer/seller.

## Findings — reasoning

> The **canonical, structured** copy of each finding lives in Airtable (`Findings` table):
> rank, status, depth, type, innocent explanation, evidence path. This section carries the
> *reasoning* — why it's deep vs shallow, why it stings, what was ruled out. Don't duplicate
> the fields here; they will drift.

**Rank 1 — full £8,000 curriculum + a live payment link to a second, unrelated program are public pre-purchase**
Depth: DEEP · Type: content/security exposure on a high-ticket sales page
Innocent explanation: the curriculum text reads like it was copy-pasted straight from the internal course-build notes, and Podia may be rendering full lesson descriptions publicly instead of titles-only — likely nobody has checked what a logged-out visitor actually sees on that page.
Why it matters: the £8,000 Dubai Boardroom Mastermind sales page shows its entire 148-lesson curriculum in full detail, pre-purchase, including a live payment link to a second, unrelated program — a real visitor never needs to pay to get the content. This is the strongest finding on the funnel (Tier A per the Funnel Walk): anyone can read the entire curriculum in full — including a live Mamopay payment link to a separate, unpriced program ("Decisionary Coach Accelerator") — without ever paying the £8,000. Show: the Dubai Boardroom Mastermind product page, scrolled to the "Link To Download My 'Decisionary Coach Accelerator' Program" lesson block — the live Mamopay payment link visible to a logged-out visitor. Fix: in Podia's course editor, switch the curriculum/contents section to titles-only for non-enrolled visitors (hide lesson descriptions), and move the Mamopay link into a gated, enrolled-only lesson instead of the public product page. Done state: a logged-out visitor sees only the 148 lesson titles — no descriptions, no links — until they buy; the Decisionary Coach Accelerator payment link only reaches actual customers being onboarded into it.

Note: this lead has a live/warm thread (Reply Received) and further back-and-forth about the precise scope of this finding exists in the Airtable Touches record — that exchange is out of scope for this document per the migration mapping (Email Thread Log is never duplicated here) and should be read there directly before this lead is re-walked in R6.

Re-walked 2026-07-25: **still present.** Fresh no-login Firecrawl scrape of the current product page confirmed the full 148-lesson curriculum still shows full lesson descriptions (not titles-only) to a logged-out visitor, and the "Link To Download My 'Decisionary Coach Accelerator' Program [My Sales Rep Training Course]" lesson block still contains the same live Mamopay payment link (`https://business.mamopay.com/pay/williambrownconsultingservices-b39ab8`), unchanged since the original walk. William has not gated or fixed this as of 2026-07-25 — outreach referencing this finding remains factually accurate today.
Evidence: [finding-1.png](./evidence/finding-1.png) (promoted 2026-07-25 re-walk screenshot; the underlying markdown capture of the specific lesson block is the stronger proof at this page length — see Evidence section above)

**Rank 2 — both checkouts are bare stock Podia carts, no order bump / guarantee / social proof** *(Tier B, per the Funnel Walk)*
Depth: SHALLOW · Type: missing checkout conversion elements
Innocent explanation: likely the default Podia checkout template, never customized since launch.
Why it matters: both checkouts (£97 course, £8,000 mastermind) are bare stock Podia carts with no order bump, guarantee, or social proof at the highest-intent moment.

Re-walked 2026-07-25 (spot-check only, per task priority): Mastermind checkout (£8,000) re-scraped — still a bare stock Podia cart, no order bump/guarantee/social proof, unchanged. Not re-verified for the £97 checkout; no evidence promoted (unused finding, lower priority).
Evidence: none promoted yet

## SMYKM Hook

`his Jul 7 post coining "genuine-uity" ("that's not a word, I made it up") to explain why two near-identical coaches earn $14K vs $271K a month` — **WORK** — source: https://www.linkedin.com/posts/william-brown-01a310182_two-coaches-nearly-identical-content-wildly-activity-7480095687779586048-846t

---

*Email history lives in Airtable (`Touches` table) — every send and reply, verbatim.
Price discovery answer and anchor live on the Airtable `Leads` record.
Neither is duplicated here.*
