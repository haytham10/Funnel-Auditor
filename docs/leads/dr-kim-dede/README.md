# Dr. Kim Dede

<!-- airtable-record: TBD -->
> **Site:** https://www.kimdede.com/ · **Profile:** https://ae.linkedin.com/in/kim-dede/en
> **Walked:** 2026-07-13 · **Slug:** `dr-kim-dede`

---

## Overview

Dr. Kim Dede — "The Female Career Coach" / The Dede Company. Career & leadership coach for women, German,
living and working in Dubai (confirmed on site + LinkedIn: "based in Dubai," Dubai skyline imagery,
client "Nadja, client in Dubai"). PhD on women in higher-management careers, ex-PwC Senior Associate,
Adjunct Professor at UE Dubai, LinkedIn Top Voice 2024. Site is Squarespace. Main offers: three 1:1
coaching packages (Confidence / Clarity / Joy), corporate keynotes, workshops and a Female Leadership
Programme; hosts the "She's Meant for More" podcast. Pricing surfaces only in a homepage FAQ ("from 235
EUR / session, packages over 3-6 months").

## Funnel Walk

- Stop 1 (Bio/Home) — clean, well-structured: hero + three labeled coaching cards + podcast + newsletter
  forms. Contains the dead HR link (see Findings).
- Stop 3 (Offer/Sales) — three package pages (confidencecoaching, clarity, offerjoy). Primary CTA =
  mailto:kimdede@thededecompany.com. No price shown on any of the three. offerjoy CTA button misreads
  "Click your to write me."
- Stop 4 (Checkout) — /cart renders but is a generic empty Squarespace cart; coaching is sold via
  mailto/forms, not cart. No leak here (empty cart is expected, not a broken checkout).
- Stop 5 (Audience ownership) — multiple working newsletter opt-ins (homepage, clarity page) + reCAPTCHA
  "Reach out now" form. Owns a list mechanism.

## Evidence

- **Site vision pass:** `VISION PASS: COMPLETE — 10 of 10 required images confirmed read`
- **Pasted evidence:** none — crawl-only walk (Notion page body was blank). Machine flags rejected in
  the vision pass: 4 — ambiguous-bio (clear), checkout-no-price (empty-cart), Spotify-JS-buttons
  (chrome), clarity-"Let's go"-button (works).
- **Screenshots:** none promoted yet — see per-finding notes below

## Gates

- **Gate 0:** Pass — UAE base confirmed (Dubai, site + LinkedIn location AE); funnel present (3 paid
  coaching packages + corporate programmes); activity strong (LinkedIn posts every 1-4 days, most recent
  1 day ago; podcast episode Jun 25); audience: LinkedIn is her primary channel (Top Voice 2024, daily
  posting) — clears the 1,500 floor on that proxy, but exact LinkedIn follower count is not exposed by
  any no-login tool (Firecrawl can't reach LinkedIn; Apify profile/posts actors don't return the count).
  IG @thefemalecareercoach = 547 (below floor, secondary channel).
- **Gate 1:** Pass — solo operator / founder of The Dede Company (small international team for corporate
  work, but she is the coach and the brand face; 1:1 coaching and inbound all route to her personally).
- **Lane:** Lane 1 (felt leak) — a live, visually-confirmed dead link on a conversion path.

## Findings — reasoning

> The **canonical, structured** copy of each finding lives in Airtable (`Findings` table): rank, status,
> depth, type, innocent explanation, evidence path. This section carries the *reasoning* — why it's deep
> vs shallow, why it stings, what was ruled out. Don't duplicate the fields here; they will drift.

**Rank 1 — Homepage HR/corporate CTA links to a 404**
Depth: DEEP · Type: dead link on the higher-ticket B2B path
Innocent explanation: she moved contact to inline forms (Get-to-know / Reach out now both work) and the
standalone /kontaktformular page was retired during that change, but the homepage HR link still points
to the old URL — a leftover from a site update.
Why it matters: the homepage's corporate/HR CTA — "Are you an HR professional and need an individual
offer for your organization? Contact me here." — links to /kontaktformular, which returns a 404. Her
B2B/keynote inquiry route dead-ends, and corporate work is her higher-ticket path. Show/Fix/Done from the
walk's Loom skeleton: Show kimdede.com homepage, the "Are you an HR professional... Contact me here."
line, then click it live to land on the /kontaktformular 404 page. Fix: in Squarespace, repoint that link
to the working on-page contact form (or the "Free Get-to-know" form), or restore/rename the
/kontaktformular page. Done state: an HR visitor clicking "Contact me here" lands on a working
corporate-inquiry form instead of a "page not found."
Evidence: [`finding-1.png`](./evidence/finding-1.png) (not yet promoted)

**Rank 2 — offerjoy CTA button reads "Click your to write me"** *(RESERVED — call bait, never emailed)*
Depth: SHALLOW · Type: copy typo
Innocent explanation: a copy edit applied to two of three near-identical pages, one missed.
Why it matters: confidencecoaching and clarity correctly read "Click here to write me"; the typo is
visible desktop + mobile on the third page.

**Rank 3 — No package page shows a price** *(RESERVED — call bait, never emailed)*
Depth: SHALLOW · Type: pricing transparency
Innocent explanation: pricing kept conversational/bespoke, a common coach choice rather than an
oversight.
Why it matters: none of the three coaching-package pages show a price; the only figure ("from 235
EUR/session, packages 3-6 months") is buried in a homepage FAQ accordion, so a visitor comparing packages
never sees cost on the offer page.

## SMYKM Hook

`Your PhD finding that men get promoted for potential while women get promoted for what they have already
proven` — **WORK** — source:
https://www.linkedin.com/posts/kim-dede_coaching-phd-women-activity-7482661207389315072-ocf5
(posted Jul 14 2026)

---

*Email history lives in Airtable (`Touches` table) — every send and reply, verbatim.
Price discovery answer and anchor live on the Airtable `Leads` record.
Neither is duplicated here.*
