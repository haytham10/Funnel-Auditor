# Charlotte (C Coaching)

<!-- airtable-record: TBD -->
> **Site:** https://www.c-coaching.consulting/for-leaders.html · **Profile:** https://www.linkedin.com/in/charlotte-verhaert-shapingyourfuture
> **Walked:** 2026-07-15 · **Slug:** `charlotte-c-coaching`

---

## Overview

Charlotte Verhaert, founder/CEO of C Coaching.Consulting (Weebly site), a Dubai-based leadership / business (high-performance executive) coach. Former senior exec at Maersk, Bolloré and Safmarine and a board director in Belgium; Certified High Performance Coach (CHPC). Main offer is a call-priced 12-session Certified High Performance Coaching program (For Leaders), plus B2B org consulting (Compass) and an annual ~9,000 AED luxury business retreat (C-Treat). Funnel is a call-booking flow (Calendly "15 Minute Call"). Owned/social reach is thin on measurable channels (Instagram 289, LinkedIn company page 70); her real channel is personal LinkedIn, which posts 2-3x/week and sized at 2,365 followers on re-confirmation (see Gates).

## Funnel Walk

- Stop 1 (Entry / For Leaders sales page) — clean, well-built: "INVEST IN YOURSELF", 12-session CHPC program, 4-step enrollment (book free discovery call → readiness questionnaire → 60-min strategic session → 12 sessions). No visible price (call-gated, fine).
- Stop 2 (Booking / Calendly) — LIVE and healthy: July 2026 calendar with real availability (20, 21, 27, 28). Not a stuck/empty calendar. (Default tz showed "Eastern Time - US" — a scrape-server artifact, not a real finding.)
- Stop 3 (Offer / C-Treat retreat) — DEAD/STALE: the page linked in the top nav of every page still sells a 3-day retreat dated "UAE FEB 19th - 21st 2026" (passed ~5 months ago) with live "YES, I'M IN" / "BOOK MY SPOT" / "APPLY NOW" buttons, an expired "EARLY BIRD OFFER ENDS NOV 30" (Nov 30 2025), and live AED pricing (9370 / early-bird 8620 single; 8870 / 8160 double). A prospect clicking C-Treat today is invited to pay for a finished event.
- Stop 4 (Audience capture) — a working contact form exists on /contact, but there is no lead-magnet / newsletter opt-in anywhere; the only next step is booking a call or the contact form.
- Stop 5 (Blog / activity) — active but cadence-gapped: latest post 4/22/2026, then 1/5/2026, 11/28/2025... The newest post's "Read More" points at a leftover template slug (/blog/test-test); others sit on default slugs (/blog/june-10th-2022, /blog/titel-van-blog-artikel-1). Cosmetic only.

## Evidence

- **Site vision pass:** `VISION PASS: COMPLETE — 12 of 12 required images confirmed read`
- **Pasted evidence:** none — crawl-only walk (Notion page had no attachments).
- **Screenshots:** none promoted yet — see per-finding notes below

## Gates

- **Gate 0:** Pass (resolved after a hold — see below). UAE base — PASS: "settled with our family in the vibrant city of Dubai" (About/Home), Dubai skyline hero, footer "Dubai UAE | +971 58 532 28 90". Funnel — PASS: live For Leaders program page + Calendly booking + C-Treat retreat sales page with AED pricing. Activity (30-day) — PASS: personal LinkedIn posts 2026-07-06 (9 days ago), 2026-06-30, 2026-06-25 (via read-only Apify); blog itself is stale (Apr 22) but LinkedIn clears the floor. Audience (1,500+) — originally UNVERIFIED at the walk (Instagram @verhaertcharlotte 289, LinkedIn company page 70, both far below 1,500); resolved 2026-07-17 by sizing her personal LinkedIn (her real channel) at **2,365 followers** via read-only Apify li-profile (Dubai, UAE) — clears the floor. Gate 0 audience = PASS as of the revival check.
- **Gate 1:** Pass — solo operator / personal brand. Everything runs off Charlotte (her name, her email, her calendar); a second coach "Amélie" and occasional "our team" language appear on the retreat/org pages but the decision-maker is unambiguously Charlotte.
- **Lane:** Lane 1 (felt leak) — a live, top-nav offer page selling a retreat that already happened. At the walk itself the finding was Lane-1 quality and visually confirmed but held at Qualifying with Finding Verified unchecked because the audience floor was unresolved; the 2026-07-17 revival check cleared the audience floor, re-verified `Email Verified` (`EMAIL VERIFY: PASS — charlotte@c-coaching.consulting: mailbox confirmed deliverable (ok)`), checked Finding Verified, and moved Status to Audit Ready.

## Findings — reasoning

**Rank 1 — Top-nav retreat page sells an event that already ran**
Depth: not specified in raw archive · Type: stale content / dead offer
Innocent explanation: she runs C-Treat annually and reuses the same page each cycle; the Feb 2026 edition ran and the page simply hasn't been rolled to the next cohort (or taken down) yet.
Why it matters: the C-Treat page invites prospects to APPLY NOW / BOOK MY SPOT for a Feb 19-21 2026 retreat that passed ~5 months ago, with expired Nov-30 early-bird pricing still shown — linked in every page's top nav, live "APPLY NOW / BOOK MY SPOT / YES I'M IN" buttons, AED pricing, and a deadline seven months gone. Anyone who clicks C-Treat today is asked to pay for a finished event.
Loom / fix path: show the C-Treat page (c-coaching.consulting/c-treat-luxurious-business-retreat-uae-2026.html) — hero "FEB 19th - 21st 2026" and the pricing cards with "EARLY BIRD OFFER ENDS NOV 30" and live APPLY NOW. Fix: in Weebly, either unpublish/redirect the C-Treat nav item until the next cohort, or swap the passed dates + Nov-30 early-bird + pricing for the next retreat and re-open applications (or route to a waitlist). Done state: a visitor clicking C-Treat sees an upcoming date they can actually apply for (or a clean waitlist), instead of being asked to pay for a retreat that already ran.
Ruled out in the vision pass: three machine flags were rejected (footer copyright year "© 2022/2021" read as a stale date — it is just a footer year; Calendly "Eastern Time - US" default tz — a scrape-server geolocation artifact; "Tap to unmute" JS buttons — video autoplay chrome) and one flag was refined (a machine "no email capture anywhere" flag was narrowed — a contact form DOES exist on /contact — to "no lead-magnet/newsletter opt-in").
Evidence: none promoted yet

**Rank 2 — No owned-list capture anywhere on the site** *(RESERVED — call bait, never emailed)*
Depth: not specified in raw archive · Type: missing list-building mechanism
Innocent explanation: a referral- and call-led business where list-building was never set up.
Why it matters: an active blog (to April) and 2-3x/week LinkedIn essays and VP interviews pull readers in, but the site's only next step is booking a call or a contact form — every reader who isn't call-ready today leaves with no way to be nurtured.
Evidence: none promoted yet

**Deep-audit reasoning (Loom / call-prep material, beyond the banked cold-outreach opener above)**

A senior-level funnel audit (`haytham-funnel-auditor`) was run 2026-07-17 against 6 live-scraped pages (Home, For Leaders, C-Treat, For Organisations/Compass, About, Contact) to prepare Loom/call material. None of this duplicates the banked C-Treat stale-date opener above (still rank 1) — it's the deeper structural layer:

- **No permission asset, no ladder (highest impact):** no lead magnet/opt-in anywhere (the Compass PDF flyer is a bare link, not gated) — the only actions on the whole site are "book a call" or "apply to C-Treat," which is a premature pitch against her actual cold/lukewarm channels (LinkedIn, blog, directories). Fix: one low-commitment asset (short PDF or a self-assessment off the existing Recognition/Energy/Purpose block) that captures an email before the call ask.
- **No guarantee anywhere** on a 9,000+ AED purchase (neither For Leaders nor C-Treat) — depresses perceived likelihood of achievement and isn't fixable with better copy alone. Fix: add explicit risk-reversal to both offers.
- **Broken price ladder:** For Leaders (the cheapest entry) shows no price at all (fully call-gated); C-Treat's 9,370 AED is the only number on the site, unanchored, with no cross-links between the three offers. Fix: show a price on For Leaders so C-Treat has something to anchor against; add one cross-sell line per offer page.
- **One-job-per-page violated on 3 of 6 pages:** For Leaders has 4 competing CTA destinations; Contact has 3 equal-weight paths to the same outcome (Calendly/mailto/form); Home has 2 competing primary CTAs. Fix: one primary CTA per page, demote the rest to text links.
- **No falsifiable proof anywhere:** the only number on the site is an unsourced "9.6/10 satisfaction rate" (For Leaders). Real proof exists and is unused as evidence: 15 years at Maersk/Bolloré/Safmarine, a Belgian board directorship, and a CHPC cert from Brendon Burchard's academy all sit in the About bio as narrative color only. Fix: pull 2-3 real career facts into For Leaders/C-Treat as proof points; cut or source the stat.
- **No single big idea sitewide:** the Home hero ("CONNECT. CREATE. CELEBRATE.") is lifted almost verbatim as C-Treat's tagline, while For Leaders runs a different promise entirely ("INVEST IN YOURSELF"). Fix: one throughline across Home/For Leaders/About.
- **Compass (B2B) has zero third-party proof** — no client logos/company names/case studies on the one page aimed at a buyer who needs to justify spend upward, a bigger gap than on the 1:1 pages (which at least carry named testimonials).
- Minor: For Leaders' 4-step enrollment gauntlet (call → questionnaire → strategic session → THEN sessions start) sits directly under genuinely painkiller-coded burnout questions — a time-delay mismatch for her most urgent buyers. Sitewide footer still reads "© 2022."

Loom talking-point order (Home → For Leaders → C-Treat → Contact): Home hero vs. For Leaders promise (two different promises, same business); For Leaders' 4 CTA destinations and missing price and the 4-step gauntlet under the burnout questions; C-Treat's 9,370 AED price with nothing above it to anchor it and no guarantee anywhere; Contact's three parallel paths side by side ("if you don't know which one to click, neither does she").

## SMYKM Hook

`she runs a recurring "Interviewing remarkable women" series on her personal LinkedIn — latest installment featured Natalia Varon Perea, VP Commercial at SSA Marine, on embracing female strength and reaching the top as a female leader` — **WORK** — source: LinkedIn post, Jul 6 2026 (li-posts pull, linkedin.com/in/charlotte-verhaert-shapingyourfuture)

---

*Email history lives in Airtable (`Touches` table) — every send and reply, verbatim.
Price discovery answer and anchor live on the Airtable `Leads` record.
Neither is duplicated here.*
