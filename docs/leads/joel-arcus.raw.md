<!--
VERBATIM ARCHIVE — DO NOT EDIT
Source: Notion page 3a2382c8-4585-811b-bc48-f387f168ea5d
Fetched: 2026-07-25T13:40:25Z
This is the unparsed original. The structured copy lives in Airtable
(Touches / Leads). If a parse is ever wrong, this is the source of truth.
-->

## Overview
Joel Arcus runs "Stay With The Question" ([stwtq.com](http://stwtq.com)), a solo life/leadership/mindset coaching practice based in Dubai, working worldwide. Custom Next.js site (not a hosted funnel builder). Main paid offer: a single 1:1 coaching session at a pre-launch \$79 (reg. \$540, code PRELAUNCH_SWTQ, offer ends Sep 30), booked via Calendly + Stripe in an embedded #coaching section on the homepage; also a free AI-coaching app (start free) and a book launching Sep 2026. 5,203 LinkedIn followers. "Powered by FalconBridge Partners" is corporate-advisory branding, not a gatekeeper on his solo coaching.
## Funnel Walk
Stop 1 (Entry/home) — full custom sales page, hero "Stay with the question," clear #coaching offer section with Calendly+Stripe embedded checkout — real funnel, not a link hub.
Stop 2 (Freebie) — /app/signup captures name+email for the free AI app before delivering — list-building present.
Stop 3 (Offer/Sales) — homepage #coaching: single session \$540 → \$79, tabs Discovery / Coaching series / Corporate enquiry.
Stop 4 (Checkout) — Calendly + Stripe embedded on the homepage offer section (no separate checkout URL to hop; JS-embedded, not click-resolvable via static fetch).
Stop 5 (Audience ownership) — newsletter + freebie email capture on every page — owns a list.
## Evidence
- Site vision pass: VISION PASS: COMPLETE — 7 of 7 required images confirmed read
- Pasted evidence: none — crawl-only walk.
- Machine flags rejected in the vision pass: 2 — blog-stale (miscomputed "126 days"; newest post 28 May 2026 \~52d, and activity floor already passed on LinkedIn 5d ago), bio-ambiguity (home is a full sales page, not a link hub).
Finding #1 rests on:
- evidence/joel-arcus/screenshots/stwtq_com_book_desktop.png — /book shows the prominent orange "Book a session — \$540 \$79" nav CTA (and a sticky floating copy) while the entire page is the book story + email capture, with no coaching/booking section.
- evidence/joel-arcus/screenshots/stwtq_com_blog_desktop.png — /blog shows the same "Book a session — \$540 \$79" nav CTA over an essay list with no coaching section.
- evidence/joel-arcus/_firecrawl_raw/2.html — /book HTML: CTA href resolves to #coaching on /book; grep confirms zero id="coaching" on the page.
- evidence/joel-arcus/_firecrawl_raw/4.html — /blog HTML: CTA href is [stwtq.com/blog#coaching](http://stwtq.com/blog#coaching); no id="coaching" on the page.
- evidence/joel-arcus/_firecrawl_raw/1.html — home HTML: id="coaching" exists (the only page the anchor resolves on), confirming the anchor is homepage-only.
Independent verification: VERIFIED — dead-anchor "Book a session — \$540 \$79" CTA confirmed on evidence/joel-arcus/_firecrawl_raw/2.html (/book) and 4.html (/blog): 3x href="#coaching" each incl. nav + sticky button, zero id/name="coaching" on both; 1.html (home) has \<section id="coaching"\> and uses absolute [https://stwtq.com/#coaching](https://stwtq.com/#coaching); screenshots stwtq_com_book_desktop.png / stwtq_com_blog_desktop.png show the button rendered (desktop, not mobile-only). Held at Qualifying: email unverified.
## Gates
Gate 0: Pass — UAE base (homepage meta "Coach Joel — Dubai, working worldwide" + pre-flight li-profile Dubai); funnel confirmed (\$79 Calendly/Stripe coaching offer live on home); activity (LinkedIn posted 5d ago); audience 5,203.
Gate 1: Pass — own-face solo operator ("Coach Joel," first-person practice copy). FalconBridge Partners is "powered by" corporate-advisory branding, not a team gatekeeper on his solo coaching.
## Lane + Finding
- Lane 1: Felt leak — a broken conversion path on the money CTA.
- Finding (#1): The pre-launch "Book a session — \$540 \$79" button is dead on /book and /blog. The CTA uses a page-relative #coaching anchor that only exists on the homepage, so on the two subpages the persistent nav button (and the sticky floating one) scroll nowhere — the discounted offer is unreachable from the exact pages the site funnels readers to (the homepage hero's primary CTA sends people to /book).
- Innocent explanation: the "Book a session" button is a shared site-nav component using a relative #coaching fragment; it was built and tested on the homepage where the coaching section lives, so nobody noticed it points at a missing anchor once the same button renders on the book and blog pages.
## Findings Bank
1. The pre-launch "Book a session — \$540 \$79" CTA is dead on /book and /blog — its #coaching anchor exists only on the homepage, so the persistent nav + sticky floating button scroll to nothing and the discounted offer is unreachable from the pages you drive readers to — innocent: a shared nav component using a relative #coaching fragment, built/tested only on the homepage where the section exists.
2. The free-app signup ("Bring your question. Start free.") stacks five separate mandatory consent checkboxes (18+, coaching-not-therapy, AI-processing, crisis, terms) before a free account can be created — heavy friction on the top-of-funnel free entry — innocent: legal/consent requirements for an AI coaching tool that were added for compliance without a second pass on signup drop-off.
## Loom Skeleton
- Show: /book (and /blog) with the "Book a session — \$540 \$79" button in the nav; click it on screen and show the page doesn't move — then show the working #coaching section on the homepage.
- Fix: point the "Book a session" nav/floating button to the absolute homepage anchor ([https://stwtq.com/#coaching](https://stwtq.com/#coaching)) instead of a page-relative #coaching, so it works from every page.
- Done state: clicking "Book a session" from the book or blog page lands the visitor on the live \$79 booking section every time.
## SMYKM Hook
SMYKM hook: His July 17 post — "Agreement is easy. Action is not." — on how a real question keeps following you (it shows up in the shower, in the car, at 2am), which is exactly why he built his Stay With The Question sessions the way he did. — WORK — source: [https://www.linkedin.com/posts/joelarcus_staywiththequestion-joelarcus-thethreshold-activity-7483702020844023808-Sd75](https://www.linkedin.com/posts/joelarcus_staywiththequestion-joelarcus-thethreshold-activity-7483702020844023808-Sd75)
## Email Thread Log
\[2026-07-21\] — Touch #1 — Subject: "agreement is easy" — Sent
Cold opener sent via Inbox 2, opening on the SMYKM hook and the Lane 1 finding (bank #1) per the row's Notes.
Reply: No reply
Next: 2026-07-24 — cold Touch 2 due (must carry the next unused Findings Bank entry, the Loom offer, or a disambiguating question — never a bare bump)
## Price Discovery
