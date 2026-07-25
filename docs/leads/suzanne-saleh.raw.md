<!--
VERBATIM ARCHIVE — DO NOT EDIT
Source: Notion page 3a0382c8-4585-81a6-8885-c11512173524
Fetched: 2026-07-25T13:41:16Z
This is the unparsed original. The structured copy lives in Airtable
(Touches / Leads). If a parse is ever wrong, this is the source of truth.
-->

## Overview
Suzanne Saleh, Dubai-based Integrative Nutrition health coach for women 40+ (perimenopause, plant-based living, weight loss). Runs on Wix. Paid ladder: 369 Liver Cleanse Kit (AED495), 30-Day Body Reset Program (Group AED1500 / Private AED2250, via Stripe + Tabby), and 1-month coaching (1500 AED / \$400). Free 30-min consultation booking is the entry mechanism. Audience: 4,868 followers on Instagram.
## Funnel Walk
Stop 1 (Bio/entry) — /health-coaching landing page links out to consultation, services, and both programs — clean.
Stop 2 (Freebie) — no dedicated opt-in/lead magnet page found; the free consultation booking form is the only entry mechanism.
Stop 3 (Offer/Sales) — /30daybodyresetprogram is the live, current sales page (AED1500/2250, Apple Pay/Google Pay/Card/Tabby badges shown). A second, stale route to the same program — /event-details/30-day-body-reset-program-group, dated Jul 2022 — is still reachable and shows "Registration is closed."
Stop 4 (Checkout) — both Stripe "Get Started" links (Group and Private) resolve to a Stripe error page: "Something went wrong — There are no valid payment methods available for this session. Please contact the merchant." Confirmed on desktop and mobile, both tiers.
Stop 5 (Audience ownership) — email capture present (newsletter signup on /about + consultation form) — she owns a list, not fully rented-reach dependent.
## Evidence
- Site vision pass: VISION PASS: COMPLETE — 16 of 16 required images confirmed read
- Pasted evidence: none attached — crawl-only walk
- Machine flags rejected in the vision pass: 2 — JS-only button destinations (BUY NOW / ENTER NOW on /services, /coaching) unconfirmed, no click-through evidence; "[loadbalancer.visitor-analytics.io](http://loadbalancer.visitor-analytics.io) is blocked" banner appearing in scraped text is a crawler ad-blocker artifact, not a real visitor issue
## Gates
Gate 0: Pass — UAE-based (Dubai-UAE address in site footer + LinkedIn + IG bio), funnel present (30-Day Body Reset Program + coaching + liver cleanse kit, real Stripe checkout), audience 4,868 (IG) — confirmed at qualify-leads stage, reconfirmed against the full crawl.
Gate 1: Pass — solo operator, no team/gatekeeper visible anywhere in the crawl.
## Lane + Finding
Lane 1: Felt leak — a live, currently-priced offer's actual checkout is broken for both tiers, on both devices.
Finding: Both "Get Started" Stripe checkout links for the 30-Day Body Reset Program (Group AED1500 / Private AED2250) return "Something went wrong — there are no valid payment methods available for this session" on desktop and mobile.
Innocent explanation: Stripe's payment-methods toggle (Apple Pay/Google Pay/Card) likely got disabled or misconfigured for that account/session, not a deliberate choice.
## Findings Bank
1. Both Stripe checkout links (Group AED1500, Private AED2250) for the 30-Day Body Reset Program error out with "no valid payment methods available for this session" on desktop and mobile — a ready-to-pay visitor cannot complete checkout on either tier right now — innocent: Stripe's payment-methods configuration likely got toggled off or misconfigured, not a deliberate change.
2. A 2022 event listing for the same 30-Day Body Reset Program ("Batch 2," dated Jul 30 – Aug 29 2022) is still live and reachable from the site, showing "Registration is closed" with no link forward to the current program page — innocent: an old Wix Events entry from a past cohort was never unpublished or redirected when the program moved to its current sales page.
## Loom Skeleton
- Show: [https://www.suzannesaleh.com/30daybodyresetprogram](https://www.suzannesaleh.com/30daybodyresetprogram) — click "Get Started" under either Group Program or Private Program.
- Fix: Reconnect/re-enable the Stripe payment methods (Apple Pay, Google Pay, Card, Tabby) for that checkout session so the button opens a working payment form instead of erroring.
- Done state: Clicking "Get Started" opens a real Stripe checkout with working payment options, instead of "Something went wrong."
## SMYKM Hook
SMYKM hook: no hook found in IG evidence (Apify pull returned profile only, no posts — likely private) — draft opens on the finding alone
## Email Thread Log
2026-07-19 — Touch #1 — Subject: "the biggest shift" — Sent
You wrote about the biggest shift in your own midlife journey a while back, letting go of trying to be perfect and choosing what actually feels good instead. Food, movement, mindset, all of it. That's the same thing you're coaching other women through now.
Anyway, the reason I'm writing is I went through your 30 Day Body Reset checkout with that in mind, and both the group option and the private one return an error the moment someone tries to pay, "no valid payment methods available," confirmed on a phone and a laptop both.
So a woman who's finally ready to commit at AED1500 or AED2250 gets that far and then can't actually give you the money. Right at the one page built to take it.
Is that a Stripe setting that got switched off, or has nobody run through the buy flow lately?
Haytham
Reply: No reply
Next: Cold Touch 2 due 2026-07-22 (carry an unused banked finding, the Loom offer, or a disambiguating question)
2026-07-22 — Touch #2 — Subject: "the biggest shift" — Sent
Hey Suzanne
Quick follow up on the checkout issue from earlier this week.
While I was in there I noticed something else. There's still a 2022 listing for the same 30 Day Body Reset Program floating around on the site, the old event page, and it just says registration is closed with nowhere else to go. So someone who finds that version first hits a dead end before they even get to the current page.
Two different broken paths into the same offer.
Happy to send over a quick rundown of both if it's useful, or if you've already got someone looking at the site, no worries either way.
Haytham
Reply: No reply
Next: Cold Touch 3 due 2026-07-28 (final cold touch, disambiguating question)
## Price Discovery
