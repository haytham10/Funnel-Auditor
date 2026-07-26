# Aina Raj

<!-- airtable-record: TBD -->
> **Site:** https://tmindscoaching.com · **Profile:** https://www.noomii.com/users/aina-raj
> **Walked:** 2026-07-13 · **Slug:** `aina-raj`

---

## Overview

Aina Raj runs Transforming Minds (tmindscoaching.com), a solo ICF PCC career / life / business coaching practice based in Dubai. The model is 1:1 consultation: the site drives visitors to a free 15-minute intro call and a contact form — there is no productized or digital checkout. Platform is WordPress + Elementor. Audience is ~41K on Instagram (@ainarajcoaching, 573 posts), with "500+ Clients" claimed and named corporate clients shown (Amazon, DHL, HSBC, Oracle, Salesforce, Talabat, Chalhoub, Mars). Footers also list India / Saudi / UK / Luxembourg / USA addresses, but she is positioned and based in Dubai.

## Funnel Walk

- Stop 1 (Home) — service tiles for Career / Life / Business / Executive / Interview / Emotional Intelligence Coaching, a corporate-services block, org logos, testimonials, FAQ, and CTAs "Contact Aina Today" / "Book A Free Intro Call" / "FREE 15-Min Session" — the tile image and title links are broken (see Findings).
- Stop 2 (Career Coaching page) — clean, content-rich: methodology, benefits, org logos, "Request A Discovery Session", FAQ. No pricing (call-based, expected). No leak.
- Stop 3 (Contact) — working Elementor form (Name / Email / Phone / Subject / Message), WhatsApp widget, email lifecoachingbyaina@gmail.com. Functional.
- Stop 4 (Checkout) — none; consultation model, no digital product or payment form (expected for this funnel type).
- Stop 5 (Audience ownership) — capture is contact form + WhatsApp only; no email opt-in or lead magnet behind the 41K IG audience.

## Evidence

- **Site vision pass:** `VISION PASS: COMPLETE — 4 of 4 required images confirmed read.`
- **Pasted evidence:** none — crawl-only walk (Notion page body was blank, no attachments).
- **Screenshots:** none promoted yet — see per-finding notes below. 3 machine flags rejected in the vision pass: noindex (artifact — live source + headers show index,follow); phone-mismatch (misread — consistent +971585848057 everywhere); blank-service-card-images (lazy-load artifact, not a real defect). Note: the /executive-coaching/ "dead link" machine flag was CONFIRMED, not rejected.

## Gates

- **Gate 0:** Pass — UAE-based (Dubai, per site + Noomii "Dubai, Dubai"); funnel present (sales pages + free-call/contact conversion); 30-day activity (active IG @ainarajcoaching, 573 posts, recent reels, "featured in Startup Times" post, LinkedIn active ~1mo); audience 41K IG (floor is 1,500).
- **Gate 1:** Pass — solo founder/operator ("solopreneur in career coaching"), personal brand, no team gatekeeper.
- **Lane:** Lane 1 (felt leak) — broken links on the primary conversion path.

## Findings — reasoning

> The **canonical, structured** copy of each finding lives in Airtable (`Findings` table):
> rank, status, depth, type, innocent explanation, evidence path. This section carries the
> *reasoning* — why it's deep vs shallow, why it stings, what was ruled out. Don't duplicate
> the fields here; they will drift.

**Rank 1 — homepage service tiles link to a broken missing-slash host**
Depth: DEEP · Type: broken link on the primary conversion path
Innocent explanation: a domain-wide find-replace or migration silently stripped the trailing slash on the body/card links — invisible to Aina because she reaches pages through the top menu (which uses correct links) and never clicks her own service tiles.
Why it matters: each service tile (Career / Life / Business / Executive / Interview / EI Coaching) links — on both the card image and its title — to a malformed URL missing the slash after ".com" (e.g. https://tmindscoaching.comcareer-coaching/), so a prospect who clicks the tile lands on a dead "site can't be reached" host. Only the small "Read More" button under each tile uses the correct URL. /executive-coaching/ additionally 301-redirects to a dead host. This was confirmed in the live server source (curl, HTTP 200 raw HTML; redirect via curl -I) — warm clicks off the highest-intent element on the homepage are silently lost.
Evidence: none promoted yet

**Rank 2 — 41K Instagram audience is driven to a call-only site with no email opt-in** *(RESERVED — call bait, never emailed)*
Depth: SHALLOW · Type: missing capture mechanism
Innocent explanation: the site was built call-first (ICF 1:1 selling), so a list-building opt-in was never added.
Why it matters: the not-ready-to-book majority of her audience leaves with nothing capturing them for later nurture.
Evidence: none promoted yet

## SMYKM Hook

`founder of Udan, hosts the CEO Cast talk show putting founders in the guest chair on servant leadership and product-market fit` — **WORK** — source: https://tmindscoaching.com/podcast/

---

*Email history lives in Airtable (`Touches` table) — every send and reply, verbatim.
Price discovery answer and anchor live on the Airtable `Leads` record.
Neither is duplicated here.*
