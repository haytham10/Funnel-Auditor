# Josh McCartney

<!-- airtable-record: TBD -->
> **Site:** https://info.joshmccartneyofficial.com/home, https://www.schooloflifeofficial.com/SOL-home-page · **Profile:** https://www.instagram.com/joshmccartneyofficial/
> **Walked:** 2026-07-17 · **Slug:** `josh-mccartney`

---

## Overview

Josh McCartney is a Dubai-based public speaking, sales, and communication coach — TEDx speaker, corporate trainer, event emcee. Solo personal brand (no team footer, first-person copy throughout). Runs two live offers on a GoHighLevel-built site: a 1:many "School of Life" community membership (AED 1,000 founding rate) and a corporate/1:1 services ladder (Starter $333/mo, Advanced $2997, Pro $4997). 32K Instagram followers (confirmed via search, not the bio claim). Recent public event Jun 26 2026 (Connection Hub, Dubai).

## Funnel Walk

- Stop 1 (Entry — info.joshmccartneyofficial.com/home) — Clean single-purpose homepage, "View all services" CTA narrows to one path. One owned lead-capture form ("Connect With Josh") also lives here — see Findings Rank 3.
- Stop 3 (Offer — School of Life, schooloflifeofficial.com/SOL-home-page) — "AED 1,000" founding-member price, framed everywhere as a one-time locked-in rate. Scarcity counter "31 of 50 remaining."
- Stop 3 (Offer — Services, info.joshmccartneyofficial.com/services) — Three priced tiers, Starter $333/mo, Advanced $2997, Pro $4997, each with an orange "BUY NOW" button.
- Stop 4 (Checkout — School of Life → FastPay Direct/Stripe) — Recurring $272.00/year subscription — contradicts the sales page's one-time framing. See Findings Rank 2.
- Stop 4 (Checkout — Services "BUY NOW") — No destination at all. cta-probe click-tested it live: no navigation, no widget, no visible change. See Findings Rank 1 (the opener).
- Stop 5 (Audience ownership) — Owned capture exists (the homepage form) — a machine flag of "no email capture anywhere" was a false miss, rejected on sight.

## Evidence

- **Site vision pass:** `VISION PASS: COMPLETE — 8 of 8 required images confirmed read`
- **Pasted evidence:** none — crawl-only walk (Notion page body was blank, no attached images)
- **Screenshots:** none promoted yet — see per-finding notes below

## Gates

- **Gate 0:** Pass — UAE base (Dubai, confirmed via search + About/footer), funnel floor (two live priced offers, AED 1,000 and $333-$4997), activity floor (Jun 26 2026 event, within 30 days), audience floor (32,000 IG, confirmed via search pre-flight).
- **Gate 1:** Pass — solo personal brand, first-person copy throughout, no "we/our team" language, no named marketing lead, no support-desk footer.
- **Lane:** Lane 1 (felt leak) — a provably broken buy path on a real priced offer.

## Findings — reasoning

**Rank 1 — "BUY NOW" buttons on the Services page have no destination at all**
Depth: DEEP — the highest-ticket tiers on the site (up to $4997/mo) have a buy button that does literally nothing.
Type: dead CTA (unbound button, no href/JS action)
Innocent explanation: the buttons may simply be mid-setup — left unbound while switching checkout providers or finishing the page build, not a deliberate paywall.
Why it matters: the Services page's three "BUY NOW" buttons (Starter $333/mo, Advanced $2997, Pro $4997) have no destination bound at all — no href, no JS action. Click-tested live via cta-probe: no navigation, no checkout widget, nothing happens. Anyone ready to pay corporate rates — the highest-value visitors on the site — has no way to complete it.
Loom skeleton (not sent, kept for a walkthrough offer): show the Services page pricing section, all three "BUY NOW" buttons, live click showing no response; fix would be binding each button to its Stripe/FastPay checkout link (the same mechanism already working on the School of Life page); done state is clicking "BUY NOW" on any of the three tiers taking the visitor straight to a working checkout for that price.
Evidence: none promoted yet.

**Rank 2 — School of Life sells "one-time" but charges recurring**
Depth: DEEP — a billing-trust break at the exact moment of payment.
Type: checkout mismatch (one-time framing vs. recurring charge)
Innocent explanation: the checkout's billing toggle may be left over from an earlier draft of the offer, not yet switched to one-time.
Why it matters: the School of Life page sells "AED 1,000" as a one-time "Founding Rate — Locked In For Life"; its own checkout shows a $272.00/year RECURRING subscription with no mention of "annual" or "recurring" anywhere on the sales page. A buyer joins believing they've locked in a single payment for life and instead sees a yearly charge — a mismatch that surfaces exactly when trust matters most.
Evidence: none promoted yet.

**Rank 3 — homepage lead-capture form's submit button reads "Button"**
Depth: SHALLOW — a styling miss, not a blocked path, but it undercuts the site's only owned capture point.
Type: unstyled builder default (invisible submit button)
Innocent explanation: likely an unfinished styling pass on the form widget, easy to miss since the fields above it work fine.
Why it matters: the homepage's only owned lead-capture form ("Connect With Josh") has a submit button that was never relabeled from the builder default — it literally reads "Button," in white text on a pale tan background, effectively invisible.
Evidence: none promoted yet.

## SMYKM Hook

`His speaker academy — the "3 days to a signature talk" intensive and the Mind Mastery training session he ran for the Driven Properties team` — **WORK** — source: https://www.instagram.com/joshmccartneyofficial/ (posts https://www.instagram.com/p/DZ7fWILjM_P/ and https://www.instagram.com/p/DSXfzyHDEml/)

---

*Email history lives in Airtable (`Touches` table) — every send and reply, verbatim.
Price discovery answer and anchor live on the Airtable `Leads` record.
Neither is duplicated here.*
