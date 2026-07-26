<!--
VERBATIM ARCHIVE — DO NOT EDIT
Source: Notion page 39c382c8-4585-81ae-922f-e8f18f2f5347
Fetched: 2026-07-25T13:39:57Z
This is the unparsed original. The structured copy lives in Airtable
(Touches / Leads). If a parse is ever wrong, this is the source of truth.
-->

## Overview
Carol Glynn runs Conscious Finance Coaching, a Dubai-based personal & business finance coaching brand serving primarily women. Ex-Big-4 (PwC Ireland, EY) and former regional CFO (AIG, Control Risks, Dubai); Fellow of Chartered Accountants Ireland, ICF-trained, qualified Life Coach. Award-winning; featured across Dubai One TV, The National, Gulf News, Khaleej Times, Arabian Business. She runs several storefronts in parallel: a Kajabi "WeareLIVE" USD sales page (the CRM Site URL) selling the 8-module "Financial Empowerment" course across 3 tiers; an older Kajabi storefront homepage selling the same course in AED; a \$135 "7 Day Financial Wellness" Kajabi mini-course; and a Squarespace brand site ([consciousfinancecoaching.com](http://consciousfinancecoaching.com)) with services, an Acuity booking calendar, a blog, and a live /digital-courses page.
## Funnel Walk
Stop 1 (WeareLIVE sales page): Clean, well-built long-form page — hero, pain checklist, founder story, 3 testimonials, 8 modules, 3-tier pricing \$358 / \$998 / \$1,850, all BUY NOW. Renders fully desktop + mobile.
Stop 2 (Checkouts x3): All three Kajabi/Stripe checkouts load and render correctly desktop + mobile; prices match the sales page (\$358/\$998/\$1,850); coupon + card fields work. No broken checkout.
Stop 3 (Lead capture): \$135 "7 Day Financial Wellness" mini-course exists as a low-ticket entry (promoted site-wide via the Squarespace announcement bar); newsletter + contact forms and a working Acuity booking calendar (3 discovery-call types) on the brand site. Prior walk's "no freebie/opt-in" was incomplete — capture exists off the sales page.
Stop 4 (Kajabi storefront homepage — the sales-page logo's target): A SECOND live sales page for the same course, priced 1,135 / 2,535 / 3,995 AED — conflicts with the USD sales page. Module cards (Modules 1-5) show broken placeholder images. FINDING.
Stop 5 (Squarespace homepage service tiles): "Personal Finance Coaching" tile image links to /services (HTTP 404) and "Workshops" tile image links to /digital-courses-and-masterclasses (HTTP 404); both render an unrelated blog grid. Correct pages are live at /personal-finance-services and /workshops. FINDING.
## Evidence
- Site vision pass: VISION PASS: COMPLETE — 16 of 16 required images confirmed read
- Pasted evidence: none — crawl-only walk (page body had no attachments).
- Machine flags rejected in the vision pass: 4 — "AED" string in checkout HTML (hex-hash false positive inside a Stripe URL), "404" string in Squarespace HTML (hex-hash false positive in asset filenames), work-with-me embedded Acuity calendar gray skeleton (scraper mid-load artifact — the direct booking page loads fully with real appointment types), and the WeareLIVE "Join the waitlist" two-step modal (orphaned/hidden, never displays on load).
## Gates
Gate 0: Pass — UAE base confirmed (Dubai; Squarespace footer "Dubai, UAE & Ireland", booking address "Conscious Finance HQ, Arjan, Dubai"). Funnel present (3 live working checkouts + \$135 mini-course + booking). Activity within 30 days via socials (LinkedIn \~4d ago / Threads Jun 2026 per prior walk); note blog cadence slowed (newest blog post Oct 2025). Audience floor: award-winning coach with national-media features across multiple platforms, comfortably exceeds 1,500 (IG follower count not scrapeable via no-login tool).
Gate 1: Pass — solo operator; own name, own face, own story, single-person brand. No gatekeeper/team.
## Lane + Finding
Lane 1 (Felt leak) — the deeper/wider look overturns the prior Lane 2: the CRM funnel (WeareLIVE + checkouts) is genuinely clean, but her broader live funnel is not.
Strongest finding: the same "Financial Empowerment" course is sold at two live prices at once — 1,135 / 2,535 / 3,995 AED on the Kajabi storefront homepage (where her own logo links) versus \$358 / \$998 / \$1,850 USD on /WeareLIVE, the AED figures running 14-41% below the USD prices at the fixed 3.67 peg (not a currency conversion).
Innocent explanation: the USD "WeareLIVE" launch page is the newer build and the original AED storefront was simply never retired or its pricing reconciled.
## Findings Bank
1. Same course, two live prices: the Kajabi storefront homepage ([mykajabi.com/](http://mykajabi.com/), the sales-page logo's target) lists the 3 tiers at 1,135 / 2,535 / 3,995 AED while /WeareLIVE lists them at \$358 / \$998 / \$1,850 USD — the AED figures run 14-41% below the USD at the fixed 3.67 peg, so a buyer who lands on the root pays up to \~40% less than one on the sales page, and the mismatch reads as untrustworthy. — innocent: the USD WeareLIVE launch page is newer and the original AED storefront was never retired or reconciled.
2. Two of four homepage service tiles on [consciousfinancecoaching.com](http://consciousfinancecoaching.com) dead-end: the "Personal Finance Coaching" tile image links to /services and the "Workshops" tile image links to /digital-courses-and-masterclasses, both HTTP 404 (an unrelated blog grid), so visitors exploring her two core services hit an error page (the small "Learn More" text on the coaching tile does resolve correctly). — innocent: pages were renamed to /personal-finance-services and /workshops in a redesign and the old tile image links were never repointed.
3. The Kajabi storefront homepage's course-module cards (Modules 1-5) render broken/placeholder image icons instead of module graphics. — innocent: images were dropped or relinked when the newer WeareLIVE page was built, leaving the old storefront's cards empty.
4. The sales page's contact line shows "[Support@consciousfinancecoaching.com](mailto:Support@consciousfinancecoaching.com)" as visible text but its mailto link points to admin@, and neither is her real personal inbox (carol@) — a prospect's question email may bounce or sit unread. — innocent: copy edited without updating the underlying mailto, a routine CMS slip.
## Loom Skeleton
- Show: Open her Kajabi storefront root ([https://consciousfinancecoaching.mykajabi.com/](https://consciousfinancecoaching.mykajabi.com/)) next to /WeareLIVE and put the two pricing tables on screen side by side — 1,135 / 2,535 / 3,995 AED versus \$358 / \$998 / \$1,850 USD for the identical three tiers.
- Fix: Pick one canonical page, retire or 301-redirect the other, and repoint the sales-page logo so every visitor lands on the same priced page.
- Done state: One price per tier everywhere — no buyer clicking the logo and finding a cheaper AED number, no trust hit from two live prices.
## SMYKM Hook
SMYKM hook: Your stance that women who understand money change everything, and that after 25+ years auditing the world's largest investment institutions what people actually lack isn't more knowledge, it's clarity — WORK — source: [https://www.linkedin.com/in/carol-glynn](https://www.linkedin.com/in/carol-glynn) (headline) + [https://www.linkedin.com/posts/carol-glynn_in-2026-one-of-the-most-common-things-my-activity-7474701706648342528-0hF7](https://www.linkedin.com/posts/carol-glynn_in-2026-one-of-the-most-common-things-my-activity-7474701706648342528-0hF7) (Jun 22 2026)
## Email Thread Log
2026-07-16 — Touch #1 — Subject: "women who understand money" — Sent
Hey Carol
Your line that women who understand money change everything reads different coming from someone who spent 25 years inside the world's biggest investment institutions first. You earned that one, you didn't borrow it.
Which is why this is worth a flag. The same financial empowerment course is showing two live prices at once. The page your own logo clicks through to lists the three tiers in dirhams. WeareLIVE lists them in dollars, up to 40% higher.
So a buyer who clicks your logo pays noticeably less than one who came through the sales page. And two prices for one thing is exactly what makes a careful person pause right at the buy, which is the opposite of the clarity you sell.
Is the dirham page just an old one that never came down, or is it meant to be live?
Haytham
Reply: No reply
Next: Cold Touch 3 due 2026-07-25 (day 9; carry an unused banked finding, the Loom offer, or a disambiguating question)
2026-07-19 — Touch #2 — Subject: "women who understand money" — Sent
Hey Carol
Another one from the same look around.
Two of the boxes on your homepage, the personal finance coaching one and the workshops one, click through to a page that doesn't exist. The real pages are live, they're just sitting at a different link, so the pictures point at the wrong place.
Someone taps the thing they came for and hits a dead end, when the page they wanted was right there the whole time.
Is that something that shifted when the site was rebuilt?
Haytham
Reply: No reply
Next: Cold Touch 3 due 2026-07-25 (day 9; carry an unused banked finding, the Loom offer, or a disambiguating question)
## Price Discovery
