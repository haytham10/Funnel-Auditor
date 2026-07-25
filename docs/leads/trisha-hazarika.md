# Trisha Hazarika

<!-- airtable-record: TBD -->
> **Site:** https://www.mentaa.com/coaches/view/TrishaHazarika · **Profile:** https://ae.linkedin.com/in/trisha-hazarika-63082917
> **Walked:** 2026-07-17 · **Slug:** `trisha-hazarika`

---

## Overview

Trisha Hazarika is a Dubai-based Sales Leadership Coach (Founder, Mimdax Business Consultants; 21+ yrs enterprise sales at IBM, Standard Chartered, GulfTalent). Her funnel entry is a profile on the Mentaa coaching marketplace (platform: Other), selling 1:1 sessions at USD 25-100 (15-60 min across three tracks) plus a paid live webinar "You Are Always Selling — Founder led Sales Success" (USD 30, Jul 23 2026). 4.91 rating, 11 reviews, 30 clients / 40 sessions. Audience: 5,512 on LinkedIn (confirmed via apify li-profile). She also runs her own site, mimdaxbusinessconsulting.com.

## Funnel Walk

- Stop 1 (Bio/entry — Mentaa coach page) — 11 near-equal nav/CTA links, no single "Start Here" — ambiguous first click, but a real profile with pricing, schedule, webinar, reviews.
- Stop 2 (Freebie) — none found — no opt-in/lead magnet in the crawled funnel (page pushes a "Free Discovery Call" instead).
- Stop 3 (Offer/Sales) — paid 1:1 coaching USD 25-100 + USD 30 webinar with live BOOK NOW — funnel floor confirmed.
- Stop 4 (Checkout) — booking is via BOOK NOW / BOOK FREE TRIAL on-platform; no separate checkout page reached (Mentaa handles it in-app).
- Stop 5 (Audience ownership) — email-subscribe capture present in footer; owns a LinkedIn channel (5,512) — not purely rented reach.

## Evidence

- **Site vision pass:** `VISION PASS: COMPLETE — 13 of 13 required images confirmed read`
- **Pasted evidence:** none — crawl-only walk (Playwright fallback; Firecrawl MCP scrape tools were not available to the walker this run — noted for the record).
- **Screenshots:** none promoted yet — see per-finding notes below. 5 machine flags rejected in the vision pass: 3x stale-date (review timestamps, not events); 1x dead-blog-links (posts render fine on /blog, URL-encoding artifact); 1x blog-quiet (newest post Jun 02 2026, she authored one Apr 24 2026). Independent verification: VERIFIED — "All booked! Please try another day" confirmed on her default availability view directly beneath her Book Free Trial / Book Now CTAs; per-coach (not platform-wide) confirmed, since another coach on the same page (Pravitha Rohit) renders live bookable slots (16:45/17:00/17:15/17:30) while Trisha shows "All booked."

## Gates

- **Gate 0:** Pass — UAE base confirmed (Mentaa Technologies Dubai + ae.linkedin + "United Arab Emirates" on profile); funnel floor confirmed (real paid offers, reachable); activity Pass (LinkedIn post 4 days ago, upcoming webinar Jul 23); audience 5,512 (li-profile).
- **Gate 1:** Pass — own face, own name, personal brand (Founder Mimdax); 1:1 coaching she delivers herself, no agency/gatekeeper.
- **Lane:** Lane 1 (felt leak) — a real, prospect-facing friction on the primary conversion path.

## Findings — reasoning

> The **canonical, structured** copy of each finding lives in Airtable (`Findings` table):
> rank, status, depth, type, innocent explanation, evidence path. This section carries the
> *reasoning* — why it's deep vs shallow, why it stings, what was ruled out. Don't duplicate
> the fields here; they will drift.

**Rank 1 — booking calendar shows "All booked! Please try another day" with no open slot**
Depth: DEEP · Type: dead/unsynced booking widget on the primary CTA
Innocent explanation: Mentaa's "view only" widget defaults to today's (booked) view and she likely hasn't synced live open slots into it — not that she's unavailable (webinar in 4 days, LinkedIn post 4 days ago). One coach on the same platform (Pravitha Rohit) does show live bookable times, so it is a per-coach sync gap, not an immovable platform limit.
Why it matters: her Mentaa "Coach Availability" scheduler renders "All booked! Please try another day" with no selectable open slot on the default view — sitting directly beneath her own "BOOK FREE TRIAL / Free Discovery Call — Up to 30 Minutes" and "BOOK NOW" CTAs, so a visitor she just invited to book a free call sees zero availability at first glance. Show: mentaa.com/coaches/view/TrishaHazarika, scroll to the "Schedule / Coach Availability" widget reading "All booked! Please try another day," immediately below the "Book Free Trial — Free Discovery Call" button. Fix: publish/sync a handful of open discovery-call slots into the Mentaa availability calendar (as the coach whose widget already shows live times has done), so the preview shows bookable times instead of "All booked." Done state: a visitor clicking Book sees open slots and books the free call in one step, instead of hitting a dead "try another day."
Evidence: none promoted yet

**Rank 2 — published testimonial still contains pasted AI prompt text** *(spent on touch 2, alongside Rank 1)*
Depth: SHALLOW · Type: unedited social proof / low-polish credibility signal
Innocent explanation: it is a client-submitted review she likely has not seen render with the artifact.
Why it matters: a testimonial in her review block opens "Here you go — 5 clean lines in English:" with raw formatting artifact left in — it reads as unedited, low-polish social proof sitting on her sales page, right where a prospect is vetting whether to trust her.
Evidence: none promoted yet

## SMYKM Hook

`Your "Friday Things" unpopular opinion on what a good discovery call actually looks like stuck with me` — **WORK** — source: https://www.linkedin.com/posts/trisha-hazarika-63082917_sales-discoverycall-businessdevelopment-activity-7483732231903985664-DVM6

---

*Email history lives in Airtable (`Touches` table) — every send and reply, verbatim.
Price discovery answer and anchor live on the Airtable `Leads` record.
Neither is duplicated here.*
