<!--
VERBATIM ARCHIVE — DO NOT EDIT
Source: Notion page 39c382c8-4585-81fc-a45f-cbedb9614bc7
Fetched: 2026-07-25T13:40:53Z
This is the unparsed original. The structured copy lives in Airtable
(Touches / Leads). If a parse is ever wrong, this is the source of truth.
-->

## Overview
Murielle Larrière runs Dubai French Tuitions, a solo online French-tutoring business she founded in 2012 and still teaches single-handedly ("Murielle is the sole teacher"). Dubai-based, native French teacher and DELF examiner, on Kajabi. Audience is 48,612 Instagram followers (verified business account) plus 15,861 on Facebook. Her IG bio link points at /vsl-access, a free-masterclass VSL, which is the real funnel entry. Published prices in AED: 2,120 (10-hour course), 2,120/m x4 (40-hour), 1,002/m x4 (Online Key Program), 233/hour (DELF prep). Real business with real students: newest Google review is 2 days old, newest blog post is Jul 06, 2026.
## Funnel Walk
Stop 1 (/vsl-access, the IG bio destination) — Wistia VSL loads fine on desktop and mobile; the ONLY call to action on the page is "Book free call" to Calendly. There is no email capture anywhere on the page — no opt-in form, no lead magnet gate. All 48K IG followers arriving here are either booking a call or leaving with nothing captured. Her IG bio promises "FREE Masterclass"; the page delivers a video plus a call booking, never a masterclass opt-in.
Stop 2 (Calendly, "Book your discovery call with Murielle") — live and functional. July 2026 shows "No times in July"; August has real bookable slots (3, 4, 6, 10, 11, 17, 18, 20, 24, 25, 27, 31). Booked out for the current month, not broken. Ruled out as a finding.
Stop 3 (/french-course-fees, the pricing page) — four price cards, all in AED, each with a "Book Now" button. This is the money page and it is where the funnel breaks.
Stop 4 (the checkouts) — every "Book Now" lands on a live Stripe checkout that charges in EUR, not AED, and two of the four point at the wrong product entirely. Confirmed by reading the four Book Now hrefs in DOM order against each checkout page:
- Card 1 "10-hour Course / 2120 AED / One time" -> offers/pnpbLYgE -> checkout reads "Learn French 40H - Private Courses (4 Instalments)", EUR 500,00 x 4 monthly payments (\~EUR 2,000 total, \~8,000 AED). Wrong product, wrong currency, \~4x the advertised price.
- Card 2 "40-hour Course / 2120 AED/m x 4 months" -> offers/VkWQUuqd -> checkout reads "Learn French 40H - Private Courses", EUR 2.000,00 EUR payable in full on registration. Right product, but the advertised 4-month payment plan becomes a single full payment at checkout.
- Card 3 "Online Key Program / 1002 AED/m x4" -> offers/92e3H2i2 -> "The French Method Beginner A1: 4xpayment", EUR 232,00 x 4. Right product, still charged in EUR.
- Card 4 "1-hour DELF Exam Prep / 233 AED/h" -> offers/VkWQUuqd -> the SAME EUR 2.000,00 40-hour course checkout as Card 2. A buyer clicking to book a single 233 AED exam-prep hour is asked for EUR 2,000 in full.
Stop 5 (/store, the Kajabi storefront, linked in her own site nav) — still on the unedited Kajabi demo template. Hero is a stock photo of a woman boxing in a gym. "Featured Courses" are the Kajabi sample fitness classes: "Core & Abs", "Fire Moves", "Aerobics 101", each with gym stock photography and placeholder copy about burning calories and building lean muscle. Every "Learn more" button links back to /store itself. "New Client Special Offers" is empty. This is on a French tutoring site.
Also noted (secondary, same page): the FAQ at the bottom of /french-course-fees contradicts the price cards directly above it — FAQ says courses "start 172 AED for a 1-hour DELF preparation class, and full courses start at 1598 AED for 10 hours", while the live cards say 233 AED/h and 2120 AED. Stale FAQ copy against current pricing.
## Evidence
- Site vision pass: VISION PASS: COMPLETE — 9 of 9 required images confirmed read (13 screenshots on disk: the 9 manifest-required plus 4 extra zoomed captures taken to read the price cards and both Calendly months at legible scale).
- Pasted evidence: none — crawl-only walk. Independent confirmation of the IG bio link and audience via a read-only, no-login Apify profile pull: 48,612 followers, verified, business account, externalUrl = [https://www.dubaifrenchtuitions.com/vsl-access](https://www.dubaifrenchtuitions.com/vsl-access), bio reads "FREE Masterclass".
- Machine flags rejected in the vision pass: 1 — Calendly "no availability" (the July markdown read as a dead calendar; the August screenshot shows a dozen live bookable dates, so the flag is dead — she is booked out, not broken).
## Gates
Gate 0: Pass — UAE base confirmed (Dubai; site, blog byline "French teacher in Dubai", Google Maps presence). Funnel floor confirmed (live Kajabi sales page with four priced offers and working Stripe checkouts). Activity floor confirmed well inside 30 days (blog post Jul 06 2026, Google review 2 days ago). Audience floor cleared 32x (48,612 IG, verified).
Gate 1: Pass — solo operator. Founded 2012 by Murielle, "Murielle is the sole teacher", the Calendly is her own personal booking link, the blog is written in her name, and the checkouts bill her products directly. No agency, no gatekeeper.
## Lane + Finding
- Lane 1: Felt leak — a live, revenue-blocking mismatch between the advertised price and what the checkout actually charges.
- Finding (visually confirmed): Her "Book Now" buttons send buyers to the wrong checkouts. The 1-hour DELF Exam Prep card advertised at 233 AED/h and the 10-hour course card advertised at 2,120 AED both land on Stripe checkouts for a different product billed in EUR — the DELF card lands on a EUR 2.000,00 full-payment 40-hour private course. Every checkout on the site charges EUR while every price on the site is quoted in AED. Separately, her /store page is still running Kajabi's demo fitness template ("Core & Abs", "Fire Moves", "Aerobics 101" with gym stock photos) on a French tutoring site.
- Innocent explanation: she set the Kajabi offers up in EUR when the business served a French/European client base, then re-priced the public pages in AED for the Dubai market without re-mapping which offer each Book Now button points to — the kind of thing that only surfaces when someone actually clicks through to pay, which she has no reason to do on her own site.
## SMYKM Hook
SMYKM hook: The French method she teaches, the one built to get a beginner speaking in 20 minutes a day rather than out of a grammar book — WORK — source: [https://www.instagram.com/p/DYQAi9BNJjY/](https://www.instagram.com/p/DYQAi9BNJjY/) (her most recent post, May 12 2026: "Discover the French method... speak French in just 20 minutes a day"; the POV stated plainly in [https://www.instagram.com/p/DPZFb_Ok7xI/](https://www.instagram.com/p/DPZFb_Ok7xI/) "Stop learning French from grammar books!")
## Email Thread Log
\[2026-07-15\] — Touch #1 — Subject: "the french method" — Sent
Hey Murielle
You built a whole method around twenty minutes a day and put your name on it. That is a real point of view about how a language gets learned, and most people teaching French do not have one.
Which is why the booking buttons are worth two minutes of your time. Your DELF exam prep is priced at 233 AED for the hour. The Book Now under it goes to a Stripe page asking for 2,000 euros, payable in full. It is the same checkout as your forty hour course.
Every price on your site is in dirhams. Every checkout behind them charges euros.
So a beginner who decides to try one hour with you gets asked for the full course instead.
Is that the wrong link, or the wrong price?
Haytham
Reply: No reply
Next: 2026-07-18 — cold Touch 2 due
## Price Discovery
2026-07-15 — Touch #1 — Subject: "the french method" — Sent (scheduled 09:00 Gulf, drafted + scheduled 2026-07-14)
Hey Murielle
You built a whole method around twenty minutes a day and put your name on it. That is a real point of view about how a language gets learned, and most people teaching French do not have one.
Which is why the booking buttons are worth two minutes of your time. Your DELF exam prep is priced at 233 AED for the hour. The Book Now under it goes to a Stripe page asking for 2,000 euros, payable in full. It is the same checkout as your forty hour course.
Every price on your site is in dirhams. Every checkout behind them charges euros.
So a beginner who decides to try one hour with you gets asked for the full course instead.
Is that the wrong link, or the wrong price?
Haytham
Reply: No reply
Gate: CRM GATE (send): PASS — Murielle Larrière (Dubai French Tuitions): finding verified, email set, sends today 6/15
Next: 2026-07-18 — Touch 2 bump. Same subject, same thread. Bump the SAME finding (no new diagnosis, free-value cap).
HELD BACK FOR TOUCH 2 / THE LOOM (deliberately not spent in Touch 1): her /store page, linked in her own site nav, is still running Kajabi's unedited demo fitness template — "Core & Abs", "Fire Moves", "Aerobics 101", gym stock photos — on a French tutoring site. Also the /french-course-fees FAQ contradicts the price cards directly above it (FAQ says "start 172 AED... 1598 AED for 10 hours"; the live cards say 233 AED/h and 2120 AED).
CORRECTION TO THE WALK (2026-07-14): the Funnel Walk's Stop 1 claim that /vsl-access has "no email capture anywhere on the page" is WRONG. Haytham asked to lead the draft on it; the page was re-fetched and read before drafting, and it DOES have an email capture form ("Fill in the information below") plus a second CTA the walk missed entirely, "REGISTER FOR THE FREE CONFERENCE". The draft was therefore built on the verified checkout finding instead. Do not use the "no email capture" claim in any follow-up — it is false. (Her hero also confirms the method is trademarked: "Discover The French Method™".)