<!--
VERBATIM ARCHIVE — DO NOT EDIT
Source: Notion page 3a0382c8-4585-817b-8e9e-eab46dc6da2a
Fetched: 2026-07-25T13:40:25Z
This is the unparsed original. The structured copy lives in Airtable
(Touches / Leads). If a parse is ever wrong, this is the source of truth.
-->

## Overview
Josh McCartney is a Dubai-based public speaking, sales, and communication coach — TEDx speaker, corporate trainer, event emcee. Solo personal brand (no team footer, first-person copy throughout). Runs two live offers on a GoHighLevel-built site: a 1:many "School of Life" community membership (AED 1,000 founding rate) and a corporate/1:1 services ladder (Starter \$333/mo, Advanced \$2997, Pro \$4997). 32K Instagram followers (confirmed via search, not the bio claim). Recent public event Jun 26 2026 (Connection Hub, Dubai).
## Funnel Walk
Stop 1 (Entry — [info.joshmccartneyofficial.com/home](http://info.joshmccartneyofficial.com/home)): Clean single-purpose homepage, "View all services" CTA narrows to one path. One owned lead-capture form ("Connect With Josh") also lives here — see Findings Bank #3.
Stop 3 (Offer — School of Life, [schooloflifeofficial.com/SOL-home-page](http://schooloflifeofficial.com/SOL-home-page)): "AED 1,000" founding-member price, framed everywhere as a one-time locked-in rate. Scarcity counter "31 of 50 remaining."
Stop 3 (Offer — Services, [info.joshmccartneyofficial.com/services](http://info.joshmccartneyofficial.com/services)): Three priced tiers, Starter \$333/mo, Advanced \$2997, Pro \$4997, each with an orange "BUY NOW" button.
Stop 4 (Checkout — School of Life → FastPay Direct/Stripe): Recurring \$272.00/year subscription — contradicts the sales page's one-time framing. See Findings Bank #2.
Stop 4 (Checkout — Services "BUY NOW"): No destination at all. cta-probe click-tested it live: no navigation, no widget, no visible change. See Findings Bank #1 (the opener).
Stop 5 (Audience ownership): Owned capture exists (the homepage form) — machine flag of "no email capture anywhere" is a false miss, rejected on sight (see Evidence).
## Evidence
- Site vision pass: VISION PASS: COMPLETE — 8 of 8 required images confirmed read
- Pasted evidence: none — crawl-only walk (Notion page body was blank, no attached images)
- Machine flags rejected in the vision pass: 1 — false miss (packet.md's Stop 5 "no email capture anywhere" flag; the homepage's "Connect With Josh" form is a real, visible email-capture field, confirmed on the desktop and mobile screenshots)
## Gates
Gate 0: Pass — UAE base (Dubai, confirmed via search + About/footer), funnel floor (two live priced offers, AED 1,000 and \$333-\$4997), activity floor (Jun 26 2026 event, within 30 days), audience floor (32,000 IG, confirmed via search pre-flight).
Gate 1: Pass — solo personal brand, first-person copy throughout, no "we/our team" language, no named marketing lead, no support-desk footer.
## Lane + Finding
Lane 1: Felt leak — a provably broken buy path on a real priced offer.
Strongest verified finding: the Services page's three "BUY NOW" buttons (Starter \$333/mo, Advanced \$2997, Pro \$4997) have no destination bound at all — no href, no JS action. Click-tested live (cta-probe): no navigation, no checkout widget, nothing happens.
Innocent explanation: the buttons may simply be mid-setup — left unbound while switching checkout providers or finishing the page build, not a deliberate paywall.
## Findings Bank
1. Three priced tiers on the Services page (\$333/mo-\$4997) have "BUY NOW" buttons with nothing behind them — anyone ready to pay corporate rates has no way to complete it — innocent: buttons may be mid-setup, left unbound during a checkout-provider switch.
2. The School of Life page sells "AED 1,000" as a one-time "Founding Rate — Locked In For Life"; its own checkout shows a \$272.00/year RECURRING subscription with no mention of "annual" or "recurring" anywhere on the sales page — innocent: the checkout's billing toggle may be left over from an earlier draft of the offer, not yet switched to one-time.
3. The homepage's only owned lead-capture form ("Connect With Josh") has a submit button that was never relabeled from the builder default — it literally reads "Button", in white text on a pale tan background, effectively invisible — innocent: likely an unfinished styling pass on the form widget, easy to miss since the fields above it work fine.
## Loom Skeleton
- Show: The Services page ([info.joshmccartneyofficial.com/services](http://info.joshmccartneyofficial.com/services)) pricing section — all three "BUY NOW" buttons, live click showing no response.
- Fix: Bind each button to its Stripe/FastPay checkout link (the same mechanism already working on the School of Life page).
- Done state: Clicking "BUY NOW" on any of the three tiers takes the visitor straight to a working checkout for that price.
## SMYKM Hook
SMYKM hook: his speaker academy — the "3 days to a signature talk" intensive and the Mind Mastery training session he ran for the Driven Properties team — WORK — source: [https://www.instagram.com/joshmccartneyofficial/](https://www.instagram.com/joshmccartneyofficial/) (posts [https://www.instagram.com/p/DZ7fWILjM_P/](https://www.instagram.com/p/DZ7fWILjM_P/) and [https://www.instagram.com/p/DSXfzyHDEml/](https://www.instagram.com/p/DSXfzyHDEml/))
## Email Thread Log
2026-07-19 — Touch #1 — Subject: "three days to a signature talk" — Sent
Hey Josh
Getting someone to a signature talk they can own, in three days, is a hard thing to promise. You actually deliver it. The Mind Mastery session you ran for the Driven team was the same thing, not a talk, but teaching people to carry themselves differently in a room.
Which is why the services page bugged me. The three tiers are there, priced and clear. But the buy buttons are dead. I clicked all three and nothing happens.
So the people most ready to pay you, the ones at the top tiers, click to buy and land nowhere.
Are those buttons mid-setup, or pointing at the wrong place?
Haytham
Reply: No reply
Next: Cold Touch 2 due 2026-07-22 (carry an unused banked finding, the Loom offer, or a disambiguating question)
2026-07-22 — Touch #2 — Subject: "three days to a signature talk" — Sent
Hey Josh
Following up on the dead buy buttons from earlier this week.
While I was checking the services page I looked at School of Life too. The sales page markets the AED 1,000 rate as a one time "Founding Rate, Locked In For Life." But the actual checkout behind it is a 272 dollar a year recurring charge, nothing on the sales page mentions annual or recurring.
So someone joins thinking they've locked in a single payment for life, then sees a yearly charge instead.
Want me to put together a short walkthrough of both, the dead buttons and the checkout mismatch, so you can see exactly what a buyer runs into?
Haytham
Reply: No reply
Next: Cold Touch 3 due 2026-07-28 (final cold touch, disambiguating question)
## Price Discovery
