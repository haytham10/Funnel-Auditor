<!--
VERBATIM ARCHIVE — DO NOT EDIT
Source: Notion page 3a0382c8-4585-814a-87ec-dad5d3df74e7
Fetched: 2026-07-25T13:41:28Z
This is the unparsed original. The structured copy lives in Airtable
(Touches / Leads). If a parse is ever wrong, this is the source of truth.
-->

## Overview
Trisha Hazarika is a Dubai-based Sales Leadership Coach (Founder, Mimdax Business Consultants; 21+ yrs enterprise sales at IBM, Standard Chartered, GulfTalent). Her funnel entry is a profile on the Mentaa coaching marketplace (platform: Other), selling 1:1 sessions at USD 25-100 (15-60 min across three tracks) plus a paid live webinar "You Are Always Selling - Founder led Sales Success" (USD 30, Jul 23 2026). 4.91 rating, 11 reviews, 30 clients / 40 sessions. Audience: 5,512 on LinkedIn (confirmed via apify li-profile). She also runs her own site, [mimdaxbusinessconsulting.com](http://mimdaxbusinessconsulting.com).
## Funnel Walk
Stop 1 (Bio/entry — Mentaa coach page): 11 near-equal nav/CTA links, no single "Start Here" — ambiguous first click, but a real profile with pricing, schedule, webinar, reviews.
Stop 2 (Freebie): none found — no opt-in/lead magnet in the crawled funnel (page pushes a "Free Discovery Call" instead).
Stop 3 (Offer/Sales): paid 1:1 coaching USD 25-100 + USD 30 webinar with live BOOK NOW — funnel floor confirmed.
Stop 4 (Checkout): booking is via BOOK NOW / BOOK FREE TRIAL on-platform; no separate checkout page reached (Mentaa handles it in-app).
Stop 5 (Audience ownership): email-subscribe capture present in footer; owns a LinkedIn channel (5,512) — not purely rented reach.
## Evidence
- Site vision pass: VISION PASS: COMPLETE — 13 of 13 required images confirmed read
- Pasted evidence: none — crawl-only walk (Playwright fallback; Firecrawl MCP scrape tools were not available to the walker this run — noted for the record).
- Machine flags rejected in the vision pass: 5 — 3x stale-date (review timestamps, not events); 1x dead-blog-links (posts render fine on /blog, URL-encoding artifact); 1x blog-quiet (newest post Jun 02 2026, she authored one Apr 24 2026).
- Independent verification: VERIFIED — "All booked! Please try another day" confirmed on her default availability view directly beneath her Book Free Trial / Book Now CTAs (screenshots/www_mentaa_com_coaches_view_TrishaHazarika_desktop.png + pages/1_mentaa-com-coaches-view-trishahazarika.txt); per-coach (not platform-wide) confirmed via screenshots/www_mentaa_com_coaches_desktop.png, where Pravitha Rohit renders live bookable slots (16:45/17:00/17:15/17:30) while Trisha shows "All booked."
## Gates
Gate 0: Pass — UAE base confirmed (Mentaa Technologies Dubai + ae.linkedin + "United Arab Emirates" on profile); funnel floor confirmed (real paid offers, reachable); activity Pass (LinkedIn post 4 days ago, upcoming webinar Jul 23); audience 5,512 (li-profile).
Gate 1: Pass — own face, own name, personal brand (Founder Mimdax); 1:1 coaching she delivers herself, no agency/gatekeeper.
## Lane + Finding
- Lane 1: Felt leak — a real, prospect-facing friction on the primary conversion path.
- Strongest finding: her Mentaa "Coach Availability" scheduler renders "All booked! Please try another day" with no selectable open slot on the default view — sitting directly beneath her own "BOOK FREE TRIAL / Free Discovery Call - Up to 30 Minutes" and "BOOK NOW" CTAs, so a visitor she just invited to book a free call sees zero availability at first glance.
- Innocent explanation: Mentaa's "view only" widget defaults to today's (booked) view and she likely hasn't synced live open slots into it — not that she's unavailable (webinar in 4 days, LinkedIn post 4 days ago). One coach on the same platform (Pravitha Rohit) does show live bookable times, so it is a per-coach sync gap, not an immovable platform limit.
## Findings Bank
1. Booking calendar on her coach page shows "All booked! Please try another day" with no open slot on the default view, right under her own free-discovery-call CTAs — a prospect prompted to book sees nothing bookable — innocent: Mentaa's view-only widget defaults to today and she hasn't synced live availability (another coach on the platform does show real slots, so it is fixable per-coach).
2. A published testimonial in her review block still contains pasted AI prompt text — Ebad's review opens "Here you go — 5 clean lines in English:" with raw  markdown left in — reads as unedited/low-polish social proof on her sales page — innocent: it is a client-submitted review she likely has not seen render with the artifact.
## Loom Skeleton
- Show: [mentaa.com/coaches/view/TrishaHazarika](http://mentaa.com/coaches/view/TrishaHazarika), scroll to the "Schedule / Coach Availability" widget reading "All booked! Please try another day," immediately below the "Book Free Trial - Free Discovery Call" button.
- Fix: publish/sync a handful of open discovery-call slots into the Mentaa availability calendar (as the coach whose widget already shows live times has done), so the preview shows bookable times instead of "All booked."
- Done state: a visitor clicking Book sees open slots and books the free call in one step, instead of hitting a dead "try another day."
## SMYKM Hook
SMYKM hook: Your "Friday Things" unpopular opinion on what a good discovery call actually looks like stuck with me — WORK — source: [https://www.linkedin.com/posts/trisha-hazarika-63082917_sales-discoverycall-businessdevelopment-activity-7483732231903985664-DVM6](https://www.linkedin.com/posts/trisha-hazarika-63082917_sales-discoverycall-businessdevelopment-activity-7483732231903985664-DVM6)
## Email Thread Log
2026-07-25 — Touch #2 — Subject: "your take on discovery calls" — Sent
Hey Trisha
Following up on the "All booked" calendar from earlier this week.
While I was in there I also noticed one of your testimonials still has pasted AI prompt text in it, right there as social proof.
Want me to record a quick video on both? Easier to point at than explain.
Haytham
Reply: No reply
Next: Awaiting reply. Bank #2 spent; Touch 3 (disambiguating question) next if she stays quiet.
## Price Discovery
