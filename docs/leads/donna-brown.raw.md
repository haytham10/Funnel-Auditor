<!--
VERBATIM ARCHIVE — DO NOT EDIT
Source: Notion page 39e382c8-4585-812f-b2a3-ccd342e7ae8c
Fetched: 2026-07-25T13:40:12Z
This is the unparsed original. The structured copy lives in Airtable
(Touches / Leads). If a parse is ever wrong, this is the source of truth.
-->

## Overview
Donna Brown is an ICF-certified life & leadership coach based in Dubai (DIFC), with an HR / Learning & Development background (intake notes a FT Emirates NBD HR role). Solo operator on a custom-built site ([dbdonnabrown.com](http://dbdonnabrown.com), hand-coded, Kit newsletter, Stripe payment links). Offers 1:1 coaching, group coaching, a manual discovery-call request, and a self-serve course line delivered as PDF: Your Core Blueprint (AED 597), three AED 797 courses, and the Complete Growth Bundle (AED 1,997). Audience not independently confirmed (namesake collisions — many Donna Browns).
## Funnel Walk
- Stop 1 (Home) — clean hero, offerings, featured courses, testimonials, Kit opt-in — coherent, no leak.
- Stop 2 (Booking /book-a-call) — custom request form (not a live calendar); "Donna will confirm your preferred time personally by email within 24 hours." Manual but functional. Success/error banners in the HTML are correctly hidden by CSS (not shown by default).
- Stop 3 (Course directory) — lists 4 courses + bundle; bundle shows "AED 2,797" struck through then "AED 1,997" with a "Save 35%" badge.
- Stop 4 (Sales pages: Your Core Blueprint, Complete Growth Bundle) — full sales copy, Stripe "Enroll Now" CTAs; no price shown on the individual sales pages (price only appears in the directory + at checkout).
- Stop 5 (Checkout — Stripe payment links) — Core Blueprint AED 597.00 and Bundle AED 1,997.00, both match the site. The Core Blueprint checkout carries an "Add to your order" bump: "The Complete Growth Bundle AED 1,997.00 — Add" — but the bundle already includes Your Core Blueprint. Both checkouts are branded "Coaching Business" / "Pay Coaching Business", not Donna Brown.
## Evidence
- Site vision pass: VISION PASS: COMPLETE — 12 of 12 required images confirmed read
- Pasted evidence: none — crawl-only walk (Notion page body was blank).
- Machine flags rejected in the vision pass: 3 — booking success-banner (hidden by CSS), Core-Blueprint "Personal Invitation" YouTube embed = wrong video "Nano Banana Pro" (section is display:none, not visible to a visitor), site-vs-Stripe price mismatch (checked — prices match).
## Gates
Gate 0: Pass — UAE base confirmed (Dubai/DIFC, site + booking page + LinkedIn "Dubai, UAE"); funnel floor clear (live Stripe checkout AED 597–1,997 + booking). Activity (site freshly built, 2026, live checkout + active Kit newsletter) and audience 1,500+ are intake-trusted, NOT independently confirmed this run (namesake collisions obscure her own channels; Apify unavailable) — defers to Haytham's pre-send review.
Gate 1: Pass — solo operator throughout ("I", "Donna will confirm your preferred time personally", single-person brand, personal @[dbdonnabrown.com](http://dbdonnabrown.com) address). No agency/gatekeeper signals.
## Lane + Finding
- Lane 1: Felt leak — a verified, visible defect at the point of purchase.
- Strongest finding (bank #1): the Your Core Blueprint checkout offers "The Complete Growth Bundle" (AED 1,997) as an order-bump add-on — but the bundle already contains Your Core Blueprint, so anyone who adds it pays for the foundation course twice (AED 597 + AED 1,997) at the moment of highest intent.
- Innocent explanation: the Stripe payment-link cross-sell was set to promote the highest-value product to lift order value, without noticing the bundle already includes the course the buyer is on — an easy Stripe "add to order" config oversight, not carelessness.
## Findings Bank
1. Core Blueprint checkout offers the full bundle (AED 1,997) as an add-on, but the bundle already contains that course — a buyer who adds it pays for the Blueprint twice, right at the point of purchase — innocent: default Stripe payment-link cross-sell set to the top product without catching the overlap.
2. The bundle's "Save 35%" badge overstates the real discount — AED 2,797 → AED 1,997 is about 29% off (and the four courses list at AED 2,988, so even the struck-through anchor is off) — innocent: a round marketing number typed in before the prices were finalized.
3. Course names don't match across the funnel — the foundation course is "Your Core Blueprint" on the cards/checkout but "The Inner Blueprint" in the bundle comparison table/curriculum, and the fourth course is "Calm is a Superpower" on the cards but "Steadiness Within" in the bundle table/hierarchy copy — a buyer comparing pages can't be sure they're the same products — innocent: courses renamed during a rebuild, with the bundle page not caught up.
4. Stripe checkout is branded "Coaching Business" / "Pay Coaching Business" rather than Donna Brown — a small trust drop the moment the card comes out — innocent: the Stripe account business name was never set to her brand.
## Loom Skeleton
- Show: the Your Core Blueprint Stripe checkout ([buy.stripe.com/7sY14n1RXdYLbgRgBFgYU03](http://buy.stripe.com/7sY14n1RXdYLbgRgBFgYU03)) — point at the "Add to your order → The Complete Growth Bundle AED 1,997" bump, then the bundle page listing Core Blueprint as included.
- Fix: in Stripe, swap that add-on for an upgrade that charges only the difference (or remove the bundle bump on the course that's already inside it) and rename the promoted product so it doesn't duplicate the item.
- Done state: a Core Blueprint buyer sees a bump that adds new value (or a true upgrade price), never the same course billed twice.
## SMYKM Hook
SMYKM hook: no hook found in public evidence — re-checked 2026-07-17 (haytham-hook-finder): LinkedIn newest post still Jan 25 2023 (3yr old), Instagram @mindset_maestro shows nothing in the last 365 days — every channel remains dormant since 2023-2024, nothing new to work from — draft opens on the finding alone
## Email Thread Log
\[2026-07-18\] — Touch #1 — Subject: "your core blueprint bundle" — Sent (Inbox 2)
Hey Donna
Went through your site, the course line is genuinely well built. Real checkout, real pricing.
One thing on the Core Blueprint checkout though. Right where someone's about to pay 597 AED, there's an add on for the Complete Growth Bundle at 1,997 AED. But that bundle already has the course inside it.
So a buyer who adds it on pays for the same thing twice, at the exact moment she's handing over her card.
Is that meant to be there, or did it get added as a cross sell before anyone caught the overlap?
Haytham
Reply: \[2026-07-18, 10:01 Dubai\] — Donna Brown \<[donna@dbdonnabrown.com](mailto:donna@dbdonnabrown.com)\>
Good Morning Haytham,
Thank you for checking with me. I appreciate your feedback and the time spent on my site, it means alot to me.
To clarify, the Core Blueprint course is already included in the course bundle, Therefore if you decide to purchase the complete bundle, you do not need to purchase Your Core Blueprint separately.
You can simply select the full bundle at checkout and you will receive Your Core Blueprint along with all the other courses included.
I appreciate you bringing this to my attention as I understand how the checkout options have caused some confusion. I will also revisit it to see how it can be improved.
Warm Regards,
Donna
\[2026-07-18\] — Touch #2 (turn-two, warm) — Subject: "Re: your core blueprint bundle" — Sent (Inbox 2)
Hey Donna
Good to know, thanks for checking so fast.
One more thing while I had the page open. The bundle badge says Save 35%, comparing 2,797 AED to 1,997 AED. The real difference works out closer to 29%. Small gap, but it's the kind of number someone doing the math before they buy will catch.
I do the small stuff on the back end for coaches like you, the pages and pricing details that quietly chip at trust while you're focused on the actual coaching. Want me to record a quick walkthrough of what I'd tighten up?
Haytham
Reply: \[2026-07-18, 22:05 Dubai\] — Donna Brown \<[donna@dbdonnabrown.com](mailto:donna@dbdonnabrown.com)\>
Hi Haytham,
Thank you for your message. How thoughtful of you. Sure happy to know what I can do better..
By the way, how did you come across my page?
Best,
Donna
\[2026-07-19\] — Touch #3 (Loom delivery + price discovery, warm) — Subject: "Re: your core blueprint bundle" — Sent (Inbox 2)
Hey Donna
To answer your question, I was looking around at coaches in Dubai and yours was one of the few with a real checkout instead of just a contact form, so I stopped to look properly.
Here it is: [https://www.loom.com/share/9333b35228e344c5b40900a5612b5ac4](https://www.loom.com/share/9333b35228e344c5b40900a5612b5ac4)
It covers the two from my emails, plus one more I found while I was in there.
Once you've watched it, I'm curious, if someone took the whole site top to bottom, everything sorted and off your plate, what would you expect that to run?
Haytham
(Loom covered findings #1 double-charge, #2 Save 35% vs 29%, #3 course-name mismatch. Bank #4 Stripe 'Coaching Business' branding held.)
Reply: No reply
Next: awaiting her price answer — log VERBATIM into Price Discovery Answer + set Discovery Anchor the moment it lands. Warm bump ~2026-07-22 if quiet.
\[2026-07-22\] — Touch #4 (warm bump) — Subject: "Re: your core blueprint bundle" — Sent (Inbox 2)
Hey Donna
Just floating this back up in case it got buried, curious to hear your number whenever you get a chance to watch the Loom.
Haytham
Reply: \[2026-07-22, 11:09 Dubai\] — Donna Brown \<[donna@dbdonnabrown.com](mailto:donna@dbdonnabrown.com)\>
Thank you Haythem.
Im very happy with my team. Best of luck to you.
Donna
Next: Closed — explicit decline, no further follow-up. Status set to Lost.
## Price Discovery
Discovery question asked \[2026-07-19, Touch #3, Inbox 2\]: "if someone took the whole site top to bottom, everything sorted and off your plate, what would you expect that to run?" Framed at whole-site scope (wider than the Track A fixes), so read her anchor in that context.
Price Discovery Answer: awaiting her reply (log her exact words verbatim, her currency, her hedges).
Discovery Anchor: not set yet.
