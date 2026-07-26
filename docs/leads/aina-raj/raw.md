<!--
VERBATIM ARCHIVE — DO NOT EDIT
Source: Notion page 39c382c8-4585-8105-b807-d0d86cd9e94a
Fetched: 2026-07-25T13:39:41Z
This is the unparsed original. The structured copy lives in Airtable
(Touches / Leads). If a parse is ever wrong, this is the source of truth.
-->

## Overview
Aina Raj runs Transforming Minds ([tmindscoaching.com](http://tmindscoaching.com)), a solo ICF PCC career / life / business coaching practice based in Dubai. The model is 1:1 consultation: the site drives visitors to a free 15-minute intro call and a contact form — there is no productized or digital checkout. Platform is WordPress + Elementor. Audience is ~41K on Instagram (@ainarajcoaching, 573 posts), with "500+ Clients" claimed and named corporate clients shown (Amazon, DHL, HSBC, Oracle, Salesforce, Talabat, Chalhoub, Mars). Footers also list India / Saudi / UK / Luxembourg / USA addresses, but she is positioned and based in Dubai.
## Funnel Walk
Stop 1 (Home) — service tiles for Career / Life / Business / Executive / Interview / Emotional Intelligence Coaching, a corporate-services block, org logos, testimonials, FAQ, and CTAs "Contact Aina Today" / "Book A Free Intro Call" / "FREE 15-Min Session" — the tile image and title links are broken (see Finding).
Stop 2 (Career Coaching page) — clean, content-rich: methodology, benefits, org logos, "Request A Discovery Session", FAQ. No pricing (call-based, expected). No leak.
Stop 3 (Contact) — working Elementor form (Name / Email / Phone / Subject / Message), WhatsApp widget, email [lifecoachingbyaina@gmail.com](mailto:lifecoachingbyaina@gmail.com). Functional.
Stop 4 (Checkout) — none; consultation model, no digital product or payment form (expected for this funnel type).
Stop 5 (Audience ownership) — capture is contact form + WhatsApp only; no email opt-in or lead magnet behind the 41K IG audience.
## Evidence
- Site vision pass: VISION PASS: COMPLETE — 4 of 4 required images confirmed read.
- Pasted evidence: none — crawl-only walk (Notion page body was blank, no attachments).
- Machine flags rejected in the vision pass: 3 — noindex (artifact — live source + headers show index,follow); phone-mismatch (misread — consistent +971585848057 everywhere); blank-service-card-images (lazy-load artifact, not a real defect). Note: /executive-coaching/ "dead link" machine flag was CONFIRMED, not rejected.
## Gates
Gate 0: Pass — UAE-based (Dubai, per site + Noomii "Dubai, Dubai"); funnel present (sales pages + free-call/contact conversion); 30-day activity (active IG @ainarajcoaching, 573 posts, recent reels, "featured in Startup Times" post, LinkedIn active ~1mo); audience 41K IG (floor is 1,500).
Gate 1: Pass — solo founder/operator ("solopreneur in career coaching"), personal brand, no team gatekeeper.
## Lane + Finding
- Lane 1: Felt leak — broken links on the primary conversion path.
- Finding (#1): On the homepage, each service tile (Career / Life / Business / Executive / Interview / EI Coaching) links — on both the card image and its title — to a malformed URL missing the slash after ".com" (e.g. [https://tmindscoaching.comcareer-coaching/](https://tmindscoaching.comcareer-coaching/)), so a prospect who clicks the tile lands on a dead "site can't be reached" host. Only the small "Read More" button under each tile uses the correct URL. /executive-coaching/ additionally 301-redirects to a dead host (tmindscoaching.combest-executive-coaching/). Confirmed in the live server source (curl, HTTP 200 raw HTML; redirect via curl -I).
- Innocent explanation: a domain-wide find-replace or migration silently stripped the trailing slash on the body/card links — invisible to Aina because she reaches pages through the top menu (which uses correct links) and never clicks her own service tiles.
## Findings Bank
1. Homepage service tiles link to a broken missing-slash host — prospects clicking the main service cards land on "site can't be reached," and only the small Read More works, so warm clicks off the highest-intent element are silently lost. — innocent: a domain-wide find-replace/migration dropped the slash on the card links; she navigates by menu, so she never sees the dead tiles.
2. A ~41K Instagram audience is driven to a call-only site with no email opt-in or lead magnet — the not-ready-to-book majority leaves with nothing capturing them for later nurture. — innocent: the site was built call-first (ICF 1:1 selling), so a list-building opt-in was never added.
## SMYKM Hook
SMYKM hook: founder of Udan, hosts the CEO Cast talk show putting founders in the guest chair on servant leadership and product-market fit — WORK — source: [https://tmindscoaching.com/podcast/](https://tmindscoaching.com/podcast/)
## Email Thread Log
\[2026-07-18\] — Touch #2 — Subject: "ceo cast" — Sent (Inbox 1)
Hey Aina
One more from when I was on the site.
You send a real crowd over from Instagram, but the only thing to do once they land is book a call. For the ones who are curious and not ready to talk yet, there's no lighter way in, so they leave. And you've no way to reach them after that.
That's most of the 41K, not the few who book this week.
Want me to show you what I'd put in front of the call for the rest?
Haytham
\[2026-07-15\] — Touch #1 — Subject: "ceo cast" — Sent
Hey Aina
Starting CEO Cast and putting founders in the guest chair, on servant leadership, on product market fit, is a different move than the 1:1 work. You went from being the one asking the questions to building the room where they get asked.
So I looked closely at your site. The service tiles on your homepage, Career, Life, Business, all of them, link to a broken version of the address with the slash missing after the .com. Click a tile and you land on a dead site can't be reached page. Only the small Read More button under it actually works.
41K people come off your Instagram and click the biggest thing on the page. They hit a wall. You'd never catch it, since you move around your own site by the menu.
Happy to send you the exact links that break. Want them?
Haytham
Reply: No reply
Next: 2026-07-18 — cold Touch 2 due
## Price Discovery