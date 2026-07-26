# Dr. Corrie Block

<!-- airtable-record: TBD -->
> **Site:** https://www.corrieblock.ae/executive-coaching-abu-dhabi/ · **Profile:** https://www.linkedin.com/in/corrieblock/
> **Walked:** 2026-07-17 · **Slug:** `dr-corrie-block`

---

## Overview

Dr. Corrie Block, Abu Dhabi-based executive/business/leadership coach — "UAE's Top Business Coach" (NYC
Journal), Amazon #1 bestselling author of 4 books (Chief Executive Coach, Love@Work, Business is
Personal, Spartan CEO), PhD/DBA, 3x TEDx speaker. Runs 1:1 executive coaching plus corporate masterclasses
(Six Pillars of Executive Performance, "Unlock the Full Potential of Your Team") and a Spartan CEO
trainer-certification/affiliate ladder. WordPress/Elementor site (corrieblock.ae mirrors corrieblock.com);
booking via a Gravity Forms consult-then-invoice B2B model, no online checkout. 1,931 LinkedIn followers;
audience floor cleared in pre-flight on public stature (press, published books, enterprise client logos).

## Funnel Walk

- Stop 1 (Entry — Executive Coaching Abu Dhabi) — clean hero, "Book Now" + "Watch My Showreel", full nav.
  No leak (Playwright desktop + mobile render clean).
- Stop 2 (Freebie) — "Free Assessment / Ready to realign?" 7 Domains Assessment quiz (Get Started →
  Typeform) works. Retired "Sneak Peek" book-PDF banner stays dead (display:none, never renders). No
  leak.
- Stop 3 (Offer — Spartan CEO masterclass /training-topics/spartan-ceo) — THE FINDING. His flagship,
  book-titled program's page opens with the WRONG program's headline and carries generic team-training
  copy — never names "Spartan CEO." See Findings below.
- Stop 3b (Offer — Six Pillars /training-topics/six-pillars-of-executive-performance) — correctly built —
  H1 "Six Pillars of Executive Performance", real program body ("inspired by Dr. Corrie Block's
  bestseller 'Spartan CEO: Six Pillars of Executive Performance'", Pillars 1-6, specific ROI stats:
  265x, 57% higher market-over-asset value, 500% productivity). This is where the real Spartan CEO
  material lives.
- Stop 3c (Leadership Training) — four programs — Six Pillars, Business is Personal, Love@Work all "Book
  Now"; Un-Distractable shows "Book (coming soon)" beside a live-looking Book Now button. Minor — banked
  #2.
- Stop 4 (Booking — /connect) — Gravity-Forms lead-capture form (name/email/business/interest), works
  cleanly, "email me directly" hello@corrieblock.com shown. No leak.
- Stop 5 (Audience ownership) — footer newsletter subscribe + Connect form + Free Assessment quiz. Owns
  capture surfaces. No rented-audience leak.

## Evidence

- **Site vision pass:** `VISION PASS: COMPLETE — 28 of 28 required images confirmed read`
- **Pasted evidence:** Haytham's verbal lead: "Spartan CEO page has some issue at the top" — CONFIRMED
  real, see finding. Machine flags rejected in the vision pass: 3 — dead-link (the ?training=
  query-param URLs "no response" are non-canonical; the real leadership-training page renders all four
  programs fine), overlap (book-page desktop Buy-button/cover overlap is a scroll/sticky-capture
  artifact; mobile stacks cleanly), stitching (Firecrawl full-page stitching chaos on Spartan CEO/entry
  pages — Playwright renders clean, same artifact refuted before). NOTE: walk run via Playwright
  (`main.py walk`), NOT Firecrawl — Firecrawl screenshots proven untrustworthy on this site.
- **Screenshots:** none promoted yet — see per-finding notes below

## Gates

- **Gate 0:** Pass — UAE-based (Abu Dhabi; parallel Dubai/Saudi/Qatar/Kuwait/Bahrain/Oman location pages
  of the same funnel), funnel confirmed (executive coaching consult + masterclasses + 4 books + priced
  Spartan CEO cert/affiliate ladder), activity + audience carried from pre-flight (1,931 LinkedIn +
  strong public stature).
- **Gate 1:** Pass — solo personal brand throughout; "email me directly" contact copy, no team/agency/
  gatekeeper language anywhere.
- **Lane:** Lane 1 (felt leak) — flagship program page presents the wrong program at the top.

## Findings — reasoning

> The **canonical, structured** copy of each finding lives in Airtable (`Findings` table): rank, status,
> depth, type, innocent explanation, evidence path. This section carries the *reasoning* — why it's deep
> vs shallow, why it stings, what was ruled out. Don't duplicate the fields here; they will drift.

**Rank 1 — Flagship "Spartan CEO" page opens with a different program's headline**
Depth: DEEP · Type: content mismatch on the named flagship offer
Innocent explanation: this masterclass page looks spun up from a generic "Unlock the Full Potential of
Your Team" template and its hero + topics were never swapped to the Spartan CEO content — easy to miss,
since the real Spartan CEO writeup already lives on the Six Pillars page and the /book/spartan-ceo page.
Why it matters: the page for his most-branded asset — /training-topics/spartan-ceo — opens with the
headline "Unlock the Full Potential of Your Team with Dr. Corrie Block" (a different, generic
masterclass) and its whole body is generic team/HR copy (Certified AI Expert, Digital Transformation,
Employee Engagement); the words "Spartan CEO" appear nowhere a visitor can see. Anyone arriving for
Spartan CEO lands on a page that never confirms or sells it. Confirmed on reliable Playwright renders
(desktop + mobile) and in raw HTML (H1 + title both "Unlock the Full Potential of Your Team") — a content
fact, not a rendering artifact. Show/Fix/Done from the walk's Loom skeleton: Show the top of
/training-topics/spartan-ceo on desktop and phone — hero reads "Masterclass / Unlock the Full Potential
of Your Team", body is generic AI/employee-engagement bullets, "Spartan CEO" nowhere; contrast with
/book/spartan-ceo and the Six Pillars page, which carry the real Spartan CEO material (six pillars + the
265x / 57% / 500% stats). Fix: swap this page's hero headline and "Topics"/"ideal for" blocks for the
actual Spartan CEO program copy already written on the Six Pillars and book pages, so the page named for
his flagship presents his flagship. Done state: a visitor landing on the Spartan CEO page immediately
sees "Spartan CEO" and the six-pillars program — matching the book and the Six Pillars page, no generic
team-masterclass mismatch at the top.
Evidence: [`finding-1.png`](./evidence/finding-1.png) (not yet promoted)

**Rank 2 — Un-Distractable shows "Book Now" but reads "coming soon" underneath**
Depth: SHALLOW · Type: mislabeled CTA
Innocent explanation: that program is still mid-launch and the button was left visible.
Why it matters: the Leadership Training page shows "Book (coming soon)" on the Un-Distractable program
while still displaying a live-looking "Book Now" button — a bookable CTA that can't actually be booked.

## SMYKM Hook

`his recent LinkedIn post that the CEO most likely to destroy their company isn't incompetent, they're
uncoachable, and the best leaders stay relentlessly coachable the way no elite athlete competes without a
coach` — **WORK** — source:
https://www.linkedin.com/posts/corrieblock_leadership-ceo-executiveleadership-activity-7482466176489680896-fIrQ

---

*Email history lives in Airtable (`Touches` table) — every send and reply, verbatim.
Price discovery answer and anchor live on the Airtable `Leads` record.
Neither is duplicated here.*
