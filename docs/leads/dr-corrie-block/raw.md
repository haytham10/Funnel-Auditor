<!--
VERBATIM ARCHIVE — DO NOT EDIT
Source: Notion page 3a0382c8-4585-8139-ae3b-ca612d38b3ad
Fetched: 2026-07-25T13:40:12Z
This is the unparsed original. The structured copy lives in Airtable
(Touches / Leads). If a parse is ever wrong, this is the source of truth.
-->

## Overview
Dr. Corrie Block, Abu Dhabi-based executive/business/leadership coach — "UAE's Top Business Coach" (NYC Journal), Amazon #1 bestselling author of 4 books (Chief Executive Coach, Love@Work, Business is Personal, Spartan CEO), PhD/DBA, 3x TEDx speaker. Runs 1:1 executive coaching plus corporate masterclasses (Six Pillars of Executive Performance, "Unlock the Full Potential of Your Team") and a Spartan CEO trainer-certification/affiliate ladder. WordPress/Elementor site ([corrieblock.ae](http://corrieblock.ae) mirrors [corrieblock.com](http://corrieblock.com)); booking via a Gravity Forms consult-then-invoice B2B model, no online checkout. 1,931 LinkedIn followers; audience floor cleared in pre-flight on public stature (press, published books, enterprise client logos).
## Funnel Walk
Stop 1 (Entry — Executive Coaching Abu Dhabi): clean hero, "Book Now" + "Watch My Showreel", full nav. No leak (Playwright desktop + mobile render clean).
Stop 2 (Freebie): "Free Assessment / Ready to realign?" 7 Domains Assessment quiz (Get Started → Typeform) works. Retired "Sneak Peek" book-PDF banner stays dead (display:none, never renders). No leak.
Stop 3 (Offer — Spartan CEO masterclass /training-topics/spartan-ceo): **THE FINDING.** His flagship, book-titled program's page opens with the WRONG program's headline and carries generic team-training copy — never names "Spartan CEO." See Lane + Finding.
Stop 3b (Offer — Six Pillars /training-topics/six-pillars-of-executive-performance): correctly built — H1 "Six Pillars of Executive Performance", real program body ("inspired by Dr. Corrie Block's bestseller 'Spartan CEO: Six Pillars of Executive Performance'", Pillars 1-6, specific ROI stats: 265x, 57% higher market-over-asset value, 500% productivity). This is where the real Spartan CEO material lives.
Stop 3c (Leadership Training): four programs — Six Pillars, Business is Personal, Love@Work all "Book Now"; Un-Distractable shows "Book (coming soon)" beside a live-looking Book Now button. Minor — banked #2.
Stop 4 (Booking — /connect): Gravity-Forms lead-capture form (name/email/business/interest), works cleanly, "email me directly" [hello@corrieblock.com](mailto:hello@corrieblock.com) shown. No leak.
Stop 5 (Audience ownership): footer newsletter subscribe + Connect form + Free Assessment quiz. Owns capture surfaces. No rented-audience leak.
## Evidence
- Site vision pass: VISION PASS: COMPLETE — 28 of 28 required images confirmed read
- Pasted evidence: none — crawl-only walk (Haytham's verbal lead: "Spartan CEO page has some issue at the top" — CONFIRMED real, see finding)
- Machine flags rejected in the vision pass: 3 — dead-link (the ?training= query-param URLs "no response" are non-canonical; the real leadership-training page renders all four programs fine), overlap (book-page desktop Buy-button/cover overlap is a scroll/sticky-capture artifact; mobile stacks cleanly), stitching (Firecrawl full-page stitching chaos on Spartan CEO/entry pages — Playwright renders clean, same artifact refuted before). NOTE: walk run via Playwright (`main.py walk`), NOT Firecrawl — Firecrawl screenshots proven untrustworthy on this site.
## Gates
Gate 0: Pass — UAE-based (Abu Dhabi; parallel Dubai/Saudi/Qatar/Kuwait/Bahrain/Oman location pages of the same funnel), funnel confirmed (executive coaching consult + masterclasses + 4 books + priced Spartan CEO cert/affiliate ladder), activity + audience carried from pre-flight (1,931 LinkedIn + strong public stature).
Gate 1: Pass — solo personal brand throughout; "email me directly" contact copy, no team/agency/gatekeeper language anywhere.
## Lane + Finding
Lane 1: Felt leak — flagship program page presents the wrong program at the top.
Strongest finding: the page for his most-branded asset — /training-topics/spartan-ceo — opens with the headline "Unlock the Full Potential of Your Team with Dr. Corrie Block" (a different, generic masterclass) and its whole body is generic team/HR copy (Certified AI Expert, Digital Transformation, Employee Engagement); the words "Spartan CEO" appear nowhere a visitor can see. Anyone arriving for Spartan CEO lands on a page that never confirms or sells it. Confirmed on reliable Playwright renders (desktop + mobile) and in raw HTML (H1 + \<title\> both "Unlock the Full Potential of Your Team") — a content fact, not a rendering artifact.
Innocent explanation: this masterclass page looks spun up from a generic "Unlock the Full Potential of Your Team" template and its hero + topics were never swapped to the Spartan CEO content — easy to miss, since the real Spartan CEO writeup already lives on the Six Pillars page and the /book/spartan-ceo page.
## Findings Bank
1. His flagship "Spartan CEO" masterclass page (/training-topics/spartan-ceo) opens with the wrong program's headline ("Unlock the Full Potential of Your Team") and generic team-training copy — the Spartan CEO program never appears on the page named for it, so Spartan-CEO intent bounces — innocent: page cloned from a generic masterclass template, hero/topics never swapped to the real Spartan CEO content that lives on the Six Pillars + book pages.
2. The Leadership Training page shows "Book (coming soon)" on the Un-Distractable program while still displaying a live-looking "Book Now" button — a bookable CTA that can't actually be booked — innocent: that program is still mid-launch and the button was left visible.
## Loom Skeleton
- Show: the top of /training-topics/spartan-ceo on desktop and phone — hero reads "Masterclass / Unlock the Full Potential of Your Team", body is generic AI/employee-engagement bullets, "Spartan CEO" nowhere; contrast with /book/spartan-ceo and the Six Pillars page, which carry the real Spartan CEO material (six pillars + the 265x / 57% / 500% stats).
- Fix: swap this page's hero headline and "Topics"/"ideal for" blocks for the actual Spartan CEO program copy already written on the Six Pillars and book pages, so the page named for his flagship presents his flagship.
- Done state: a visitor landing on the Spartan CEO page immediately sees "Spartan CEO" and the six-pillars program — matching the book and the Six Pillars page, no generic team-masterclass mismatch at the top.
## SMYKM Hook
SMYKM hook: his recent LinkedIn post that the CEO most likely to destroy their company isn't incompetent, they're uncoachable, and the best leaders stay relentlessly coachable the way no elite athlete competes without a coach — WORK — source: [https://www.linkedin.com/posts/corrieblock_leadership-ceo-executiveleadership-activity-7482466176489680896-fIrQ](https://www.linkedin.com/posts/corrieblock_leadership-ceo-executiveleadership-activity-7482466176489680896-fIrQ)
## Email Thread Log
2026-07-25 — Touch #2 — Subject: "the uncoachable ceo" — Sent
Hey Corrie
Following up on the Spartan CEO page opening with the wrong headline from earlier this week.
While I was in there I also noticed the Leadership Training page has a Book Now button that actually reads "coming soon" underneath, so it looks live but can't be booked.
Want me to record a quick video on both? Easier to point at than explain.
Haytham
Reply: No reply
Next: Awaiting reply. Bank #2 spent; Touch 3 (disambiguating question) next if she stays quiet.
## Price Discovery
