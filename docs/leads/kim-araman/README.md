# Kim Araman

<!-- airtable-record: TBD -->
> **Site:** https://blueprint.nailyourinterview.com/the-blueprint-IG · **Profile:** https://ae.linkedin.com/in/kim-araman/en
> **Walked:** 2026-07-13 · **Slug:** `kim-araman`

---

## Overview

Kim Araman, founder of Nail Your Career — career and leadership coach in Dubai, ex-Ferrero/Unilever/Kellogg brand manager. LinkedIn Top Voice, Forbes Coaches Council, "Top #2 Career Coach in the UAE." 65,492 LinkedIn followers, posting near-daily (last post 10 hours before this walk). Small IG (1,491). She runs two separate stacks: a GoHighLevel/LeadConnector sales page at blueprint.nailyourinterview.com selling The Interview Mastery Blueprint ($291 / 1,121 AED), and an older ClickFunnels site on the root domain nailyourinterview.com carrying the free e-book, Career LaunchPad 3.0, and a Typeform strategy-call application. Checkout is Zbooni (a UAE chat-commerce platform). Solo operator — she delivers the coaching herself.

## Funnel Walk

- Stop 1 (Bio/entry) — Instagram bio link points to blueprint.nailyourinterview.com/the-blueprint-IG; LinkedIn About points to the root ClickFunnels site and then says "or just Reach out on Linkedin Messages" — two audiences, two different destinations.
- Stop 2 (Freebie) — ClickFunnels e-book opt-in (The Career Map Method) captures email before delivery. Working. Body copy renders unmerged personalization placeholders on the live page: "Like it helped [FirstName]... And [FirstName]..." See also the separately-noted freebie delivery issue below.
- Stop 3 (Offer/Sales) — The Interview Mastery Blueprint page is live, well-built, strong proof (video testimonials, named clients, 95% success rate). Priced $291 / 1,121 AED. Every CTA on the page ("ACCESS THE BLUEPRINT NOW", "ACCESS THE BLUEPRINT FOR JUST $291!") points to one Zbooni URL.
- Stop 4 (Checkout) — DEAD. That Zbooni URL returns a hard HTTP 404 and renders Zbooni's error page: "Ooops! We couldn't find what you're looking for..." Confirmed on desktop and mobile, and independently by curl (404 on the product URL, 200 on the store root — so this is a removed product, not an outage or a bot wall). Her Zbooni store itself is alive ("Nail Your Career", Dubai, 4.3 / 51 ratings, © 2026) and its "All Items" list contains exactly one product: Career Coaching Program - 6 Sessions, AED 13,212.00, badged Sold out. The Blueprint is not listed at all. Net: there is currently no way to buy anything from Kim Araman.
- Stop 5 (Audience ownership) — Owns a list (e-book opt-in + email capture). Not purely dependent on rented reach.
- Secondary (root ClickFunnels site) — Renders fine, not "dead" as an earlier qualifying pass suspected, but it is stale: footer reads "Copyright 2021® Nail Your Career"; the middle card of the three-way "Start Your Journey" block ("Masterclass 3 Step Methods To Land Your Dream Job") has a "Stay Tuned" placeholder button under copy urging "Save your spot right now before the slots all get filled up!"; Career Programs shows "Upcoming Programs — COMING SOON" and lists no price anywhere; and every page leaks the literal builder instruction "Paste this script under the activation codes above" at the bottom of the live page.

## Evidence

- **Site vision pass:** `VISION PASS: COMPLETE — 10 of 10 required images confirmed read` (13 screenshots on disk; the 2 Zbooni-404 captures and the freebie mobile sit outside the required-10 manifest and were read as well.)
- **Pasted evidence:** none — crawl-only walk. No images were attached to this page.
- **Screenshots:** none promoted yet — see per-finding notes below

## Gates

- **Gate 0:** Pass — UAE base confirmed (Dubai: Zbooni store header, LinkedIn location, Forbes Councils profile). Funnel exists (live sales page + priced digital product). Activity floor cleared hard (LinkedIn post 2026-07-14, 10 hours before the walk; near-daily posting through the last month). Audience floor cleared 44x (65,492 on LinkedIn).
- **Gate 1:** Pass — solo operator. "Founder of Nail Your Career," coaches 1:1 herself, no team, no gatekeeper, no agency layer. She personally answers LinkedIn DMs and every post ends with "send me a message."
- **Lane:** Lane 1 (felt leak) — her only buy button is broken and she is still driving traffic to it.

## Findings — reasoning

**Rank 1 — the entire funnel currently has nothing buyable (visually confirmed)**
Depth: DEEP — this is a complete purchase-path failure, not a single broken link: the flagship checkout 404s and the one remaining product in her store is marked Sold out.
Type: dead checkout + no purchasable inventory (removed/migrated product)
Innocent explanation: she almost certainly rebuilt or migrated the product on Zbooni (the store is live and the old product slug simply no longer resolves), and nobody has clicked her own buy button since — the page still looks perfect from the outside.
Why it matters: the checkout on her live $291 funnel returns a Zbooni 404, and her Zbooni store's one remaining product is marked Sold out — so at this moment there is nothing anyone can actually purchase from her, while her Instagram bio link points straight at that funnel and she posts to 65K LinkedIn followers daily. Three machine flags were rejected on the vision pass and not banked: a testimonial-date flag ("Hope 2023 is better for all of us" is text inside a WhatsApp testimonial screenshot, not a stale offer date), a harvested-email flag (chenowith52@gmail.com / test@test.com etc. live inside the ClickFunnels email-typo-suggestion JS library, not her contact details), and a "root-domain-dead" theory from an earlier qualifying pass (the root ClickFunnels page renders fully and is functional; it is stale-dated and has placeholder CTAs, but it is not dead, so that framing does not survive as the finding — the stale/placeholder details are recorded above as funnel-walk context, not banked as a separate finding since they weren't ranked in a Findings Bank).
Evidence: none promoted yet.

**Rank 2 — the freebie opt-in captures an email and appears to send nothing** *(human-observed, NOT machine-verified — see caveat)*
Depth: DEEP if confirmed — the free e-book is the only part of her funnel that still functions at all (the paid checkout 404s), so a silent list is the single working asset going nowhere.
Type: possible broken email delivery (freebie opt-in → no confirmation email)
Innocent explanation: she likely set the freebie up with redirect-delivery (instant download, no email step), which is a legitimate design choice that trades the list for a smoother user experience. She may not realize the address is being collected into a list nobody mails.
Why it matters: this finding was found on 2026-07-14 by hand — Haytham opted into the freebie at nailyourinterview.com/freebie-book1691158605156 as a real prospect would; the form took his address, redirected straight to a page with a download button, and no email ever arrived. She has 65,492 LinkedIn followers and posts daily, so everyone who downloads that e-book hands over an address and gets nothing back — either the list isn't being built, or it's being built and never mailed. **This finding is explicitly NOT visually confirmed by the machine walk and is NOT the basis of `Finding Verified`** (which stays unchecked for this angle — she has no reachable email address for outreach on this angle regardless). Two things were flagged as still needing confirmation before it's used in a draft: whether the confirmation email landed in spam/promotions after a delay (a slow or misfiled email is a much smaller finding than one that never sends), and whether the download button itself worked (if the e-book downloads fine, redirect-delivery is a deliberate, defensible choice; if it also fails, the funnel is broken end to end). It is recorded here so it isn't lost, and because it would be the stronger of the two openers if it's ever independently confirmed.
Evidence: none promoted yet.

## SMYKM Hook

`Her post yesterday about the senior professional who told her "I think I missed my window" and her line that too late is rarely a fact, it is usually just fear wearing a more reasonable disguise` — **WORK** — source: https://www.linkedin.com/posts/kim-araman_someone-sent-me-a-message-last-week-that-activity-7482661556183539712-_hQ8

---

*Email history lives in Airtable (`Touches` table) — every send and reply, verbatim.
Price discovery answer and anchor live on the Airtable `Leads` record.
Neither is duplicated here.*
