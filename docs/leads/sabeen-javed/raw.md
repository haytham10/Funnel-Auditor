<!--
VERBATIM ARCHIVE — DO NOT EDIT
Source: Notion page 3a0382c8-4585-81b6-a2ee-cdd186cbf67b
Fetched: 2026-07-25T13:40:59Z
This is the unparsed original. The structured copy lives in Airtable
(Touches / Leads). If a parse is ever wrong, this is the source of truth.
-->

## Overview
Sabeen Javed ("SJ Coaching") — British ICF-qualified career & leadership coach for women in tech/business and working mums, based in Dubai. Ex-Amazon senior recruitment leader, 18+ years across Getty Images, Samsung, Coca-Cola, Amazon. Solo personal brand on her own WordPress site ([sabeenjaved.com](http://sabeenjaved.com)) with a six-offer service menu (Leadership Readiness Report, 1:1 Coaching, 12-week Career Elevation Program, Work Triage Clinic, CV & LinkedIn Review, New Manager Training) plus a corporate "Organisations" track. Books via a personal Calendly "free discovery call". LinkedIn audience 17,583.
## Funnel Walk
- Stop 1 (Bio/Home) — 5 near-equal nav destinations, no "start here"; hero headline + primary CTA present in DOM but not legible on desktop (see Lane + Finding).
- Stop 2 (Freebie) — none found; no opt-in/lead magnet page anywhere in the funnel. Email capture is only a contact form.
- Stop 3 (Offer/Sales — /services/) — six distinct paid offers, no price on any, no buy/enroll button; each routes to a free call, a quiz, or a form.
- Stop 4 (Checkout) — not reached; no checkout or payment path anywhere (call-booked model; not itself a leak).
- Stop 5 (Audience ownership) — owns a contact-form list mechanism; not purely rented reach.
## Evidence
- Site vision pass: VISION PASS: COMPLETE — 8 of 8 required images confirmed read
- Independent verification: VERIFIED — desktop hero headline + 'Book a free discovery call' CTA washed-out/illegible on desktop vs crisp on mobile confirmed on evidence/sabeen-javed/screenshots/sabeenjaved_com_desktop.png (background/gradient/logo fully rendered, not a mid-load artifact) and sabeenjaved_com_mobile.png
- Pasted evidence: none — crawl-only walk.
- Machine flags rejected in the vision pass: 2 — email `coaching@sabeenjaved.com%20` (URL-encoding artifact; real address is [coaching@sabeenjaved.com](mailto:coaching@sabeenjaved.com)); Calendly blank-space on home/services (embed-load warning, NOT treated as a missing-CTA finding).
## Gates
Gate 0: Pass — UAE base confirmed (Dubai; +971 521240256; "UAE-based? Yes" in contact form). Funnel floor confirmed (six real, reachable paid offers on /services/, not login-walled). Activity within last month (confirmed at qualifying). Audience 17,583 on LinkedIn (apify li-profile), clears the 1,500 floor.
Gate 1: Pass — own name/face, personal "I am Sabeen" brand, personal Calendly. No agency/"we"/gatekeeper.
## Lane + Finding
- Lane 1: Felt leak — a fixable, visually-confirmed entry-page problem with a clean innocent explanation.
- Strongest finding (bank #1): On desktop, the homepage hero headline ("Career coaching for women in tech & business") and the primary "Book a free discovery call" button render washed-out and effectively illegible against the dark hero banner — the very first thing a laptop visitor sees above the fold is a broken-looking hero with an invisible primary CTA. The identical hero renders crisp and fully legible on mobile, which rules out a capture artifact and points to a real desktop-only contrast/render issue.
- Innocent explanation: she almost certainly builds and checks the site on her phone (mobile is pixel-perfect), so she has never seen the desktop breakpoint the way a laptop visitor does — the hero background sits behind the text at near-equal luminance only at desktop width.
## Findings Bank
1. Desktop homepage hero headline + primary "Book a free discovery call" CTA render washed-out/illegible against the dark banner on desktop while crisp on mobile — a laptop visitor's first impression above the fold is a broken hero with an invisible primary CTA — innocent: site built/checked on mobile, desktop breakpoint never seen.
2. The /services/ page lists six near-equal paid offers with no price on any and no purchase/checkout path — every CTA routes to a free call, quiz, or form, so a ready buyer of the productized Leadership Readiness Report or Work Triage Clinic has no way to buy and no price signal — innocent: deliberately call-first, but it strands the low-ticket productized offers that could sell self-serve.
3. Six services carry six different CTA verbs (Take the quiz / Find out more / Have a peek / Check it out / Reserve my spot / Book a training) with no "start here" primary path on either home or services — choice overload / ambiguous first click — innocent: menu grew offer-by-offer without a single front-door decision being designed.
## Loom Skeleton
- Show: [sabeenjaved.com](http://sabeenjaved.com) on a desktop/laptop window — the top hero band, headline + "Book a free discovery call" button barely visible; then the same page on a phone where it looks perfect.
- Fix: in the WordPress hero block, add/darken the background overlay (or set an explicit light text colour) at the desktop breakpoint so the H1 and CTA button clear the background.
- Done state: the headline and the pink "Book a free discovery call" button read cleanly the instant a laptop visitor lands — same first impression her phone already gives.
## SMYKM Hook
SMYKM hook: Saw you just opened applications for the Founding Cohort — five software engineers repositioning out of 'I don't want to write code forever' and into AI transformation leadership. — WORK — source: [https://www.linkedin.com/posts/sabeen-javed-career-coach_i-dont-want-to-write-code-foreveris-activity-7479051391408451584-eGOE](https://www.linkedin.com/posts/sabeen-javed-career-coach_i-dont-want-to-write-code-foreveris-activity-7479051391408451584-eGOE)
## Email Thread Log
2026-07-25 — Touch #2 — Subject: "your founding cohort" — Sent
Hey Sabeen
Following up on the illegible hero from earlier this week.
While I was in there I also went through your services page. Six offers, no price on any of them, and every button routes to a free call or a form instead of a way to actually buy. Someone ready to pay right now has nowhere to do it.
Want me to record a quick video on both? Easier to point at than explain.
Haytham
Reply: No reply
Next: Awaiting reply. Bank #2 spent; Touch 3 (disambiguating question) next if she stays quiet.
## Price Discovery
