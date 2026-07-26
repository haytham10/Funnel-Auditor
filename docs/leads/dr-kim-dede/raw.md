<!--
VERBATIM ARCHIVE — DO NOT EDIT
Source: Notion page 39c382c8-4585-8187-8313-c668426c5267
Fetched: 2026-07-25T13:40:12Z
This is the unparsed original. The structured copy lives in Airtable
(Touches / Leads). If a parse is ever wrong, this is the source of truth.
-->

## Overview
Dr. Kim Dede — "The Female Career Coach" / The Dede Company. Career & leadership coach for women, German, living and working in Dubai (confirmed on site + LinkedIn: "based in Dubai," Dubai skyline imagery, client "Nadja, client in Dubai"). PhD on women in higher-management careers, ex-PwC Senior Associate, Adjunct Professor at UE Dubai, LinkedIn Top Voice 2024. Site is Squarespace. Main offers: three 1:1 coaching packages (Confidence / Clarity / Joy), corporate keynotes, workshops and a Female Leadership Programme; hosts the "She's Meant for More" podcast. Pricing surfaces only in a homepage FAQ ("from 235 EUR / session, packages over 3-6 months").
## Funnel Walk
- Stop 1 (Bio/Home) — clean, well-structured: hero + three labeled coaching cards + podcast + newsletter forms. Contains the dead HR link (see Lane).
- Stop 3 (Offer/Sales) — three package pages (confidencecoaching, clarity, offerjoy). Primary CTA = [mailto:kimdede@thededecompany.com](mailto:kimdede@thededecompany.com). No price shown on any of the three. offerjoy CTA button misreads "Click your to write me."
- Stop 4 (Checkout) — /cart renders but is a generic empty Squarespace cart; coaching is sold via mailto/forms, not cart. No leak here (empty cart is expected, not a broken checkout).
- Stop 5 (Audience ownership) — multiple working newsletter opt-ins (homepage, clarity page) + reCAPTCHA "Reach out now" form. Owns a list mechanism.
## Evidence
- Site vision pass: VISION PASS: COMPLETE — 10 of 10 required images confirmed read
- Pasted evidence: none — crawl-only walk (Notion page body was blank).
- Machine flags rejected in the vision pass: 4 — ambiguous-bio (clear), checkout-no-price (empty-cart), Spotify-JS-buttons (chrome), clarity-"Let's go"-button (works).
## Gates
Gate 0: Pass — UAE base confirmed (Dubai, site + LinkedIn location AE); funnel present (3 paid coaching packages + corporate programmes); activity strong (LinkedIn posts every 1-4 days, most recent 1 day ago; podcast episode Jun 25); audience: LinkedIn is her primary channel (Top Voice 2024, daily posting) — clears the 1,500 floor on that proxy, but exact LinkedIn follower count is not exposed by any no-login tool (Firecrawl can't reach LinkedIn; Apify profile/posts actors don't return the count). IG @thefemalecareercoach = 547 (below floor, secondary channel).
Gate 1: Pass — solo operator / founder of The Dede Company (small international team for corporate work, but she is the coach and the brand face; 1:1 coaching and inbound all route to her personally).
## Lane + Finding
- Lane 1: Felt leak — a live, visually-confirmed dead link on a conversion path.
- Finding (bank #1): The homepage's corporate/HR CTA — "Are you an HR professional and need an individual offer for your organization? Contact me here." — links to /kontaktformular, which returns a 404. Her B2B/keynote inquiry route dead-ends, and corporate work is her higher-ticket path.
- Innocent explanation: she moved contact to inline forms (Get-to-know / Reach out now both work) and the standalone /kontaktformular page was retired during that change, but the homepage HR link still points to the old URL — a leftover from a site update.
## Findings Bank
1. Homepage HR/corporate CTA "Contact me here." (for "an individual offer for your organization") links to /kontaktformular -> 404; the corporate/keynote inquiry path dead-ends — innocent: contact moved to inline forms and the old page URL was left linked after a site update.
2. offerjoy sales-page primary CTA button reads "Click your to write me" (typo; confidencecoaching and clarity correctly read "Click here to write me"), visible desktop + mobile — innocent: a copy edit applied to two of three near-identical pages, one missed.
3. None of the three coaching-package pages show a price; the only figure ("from 235 EUR/session, packages 3-6 months") is buried in a homepage FAQ accordion, so a visitor comparing packages never sees cost on the offer page — innocent: pricing kept conversational/bespoke, a common coach choice rather than an oversight.
## Loom Skeleton
- Show: [kimdede.com](http://kimdede.com) homepage, the "Are you an HR professional... Contact me here." line, then click it live to land on the /kontaktformular 404 page.
- Fix: in Squarespace, repoint that link to the working on-page contact form (or the "Free Get-to-know" form), or restore/rename the /kontaktformular page.
- Done state: an HR visitor clicking "Contact me here" lands on a working corporate-inquiry form instead of a "page not found."
## SMYKM Hook
SMYKM hook: Your PhD finding that men get promoted for potential while women get promoted for what they have already proven — WORK — source: [https://www.linkedin.com/posts/kim-dede_coaching-phd-women-activity-7482661207389315072-ocf5](https://www.linkedin.com/posts/kim-dede_coaching-phd-women-activity-7482661207389315072-ocf5) (posted Jul 14 2026)
## Email Thread Log
2026-07-16 — Touch #1 — Subject: "promoted for potential" — Sent
Hey Kim
The potential-versus-proof gap you found, men moving up on promise while women wait until it's already done, that's not a hot take, it's your actual research. That carries a weight most career advice doesn't.
Which is why this is worth flagging. On your homepage, the invitation for HR teams to reach out about something for their organization goes to a page that 404s.
So the corporate route, your higher-value work, is the one door on the site that opens onto nothing. An HR lead who was ready to ask hits a dead end and doesn't come back to try again.
Is that link pointing at an old page, or did the form move?
Haytham
Reply: No reply
Next: Cold Touch 3 due 2026-07-25 (day 9; carry an unused banked finding, the Loom offer, or a disambiguating question)
2026-07-19 — Touch #2 — Subject: "promoted for potential" — Sent
Hey Kim
Small one, but it's on a page that matters.
On your joy coaching page, the button people click to write to you reads "click your to write me." Looks like a word got swapped by accident. Your other coaching pages have it right, which is why this one stands out.
It's the kind of thing a careful buyer notices right before they reach out, and it makes them hesitate for a second when you want the opposite.
Worth a quick look while you're in there?
Haytham
Reply: No reply
Next: Cold Touch 3 due 2026-07-25 (day 9; carry an unused banked finding, the Loom offer, or a disambiguating question)
## Price Discovery
