# Avneet Kohli

<!-- airtable-record: TBD -->
> **Site:** http://www.avneetkohli.com/ · **Profile:** https://www.noomii.com/users/avneet-kohli
> **Walked:** 2026-07-16 · **Slug:** `avneet-kohli`

---

## Overview

Avneet Kohli is a solo Business Coach / Founder Advisor based in Abu Dhabi (also spends time in Mumbai), running her own site on Wix. She positions as a "Venture Catalyst, UAE Market Enabler, Business Coach for Women Founders" with a 1:1 Business Advisory & Coaching offer (Calendly booking) plus a paid product, the Life Planner (a self-guided planning toolkit, real price $30.22 via Stripe, ships to the UAE). 22,748 LinkedIn followers, posted within the last week of qualifying — active. ICF-credentialed, solo operator throughout the funnel. This is a warm lead: she has been replying same-day since 2026-07-20 and has asked directly what Haytham does.

## Funnel Walk

Re-walked 2026-07-20 (prompted by her reply confirming she'd fixed most of what was flagged — confirming what actually changed before any further touch):

- Stop 1 (Bio/Homepage) — the header/top-nav logo (flagged in an earlier touch) now correctly links home — fixed. But the site's separate FOOTER logo (bottom of every homepage view, and of https://www.avneetkohli.com/blank itself) still links to https://www.avneetkohli.com/blank, the same orphaned old-design duplicate of the whole site — same defect class, different element, still live.
- Stop 3 (Offer/Sales — lifeplanner) — RESOLVED. All three order buttons ("ORDER MY COPY" x2, "ORDER A COPY" x1) now route to live Stripe checkout links (buy.stripe.com); the old Wix test-SKU checkout page (https://www.avneetkohli.com/product-page/test) now returns a hard 404. The AED 9.00 test-SKU issue flagged earlier no longer exists.
- Contact page — unchanged: the visible email link still reads "ak@avneetkohli.com" but its mailto target is still "info@avneetkohli.com" — still live, still unused as a touch.

## Evidence

- **Site vision pass:** `VISION PASS: COMPLETE — 3 of 3 required images confirmed read`
- **Pasted evidence:** none — crawl-only re-walk (homepage, lifeplanner, contact, 2026-07-20).
- **Screenshots:** none promoted yet — see per-finding notes below. No machine flags were rejected in this re-walk's vision pass.

## Gates

- **Gate 0:** Pass — unchanged since original walk (UAE-based, 22,748 LinkedIn followers clears the audience floor, funnel confirmed live with a working Stripe checkout, and she's actively replying same-day, well inside the activity floor).
- **Gate 1:** Pass — unchanged, solo operator throughout ("I'll get back to you personally," personal replies from her own inbox).
- **Lane:** Lane 1 (felt leak) — still holds after the re-walk. Two open items survive both filters (the contact email mismatch and a newly-confirmed footer-logo instance of the same /blank link); the two earlier findings that drove the first two touches are both resolved.

## Findings — reasoning

> The **canonical, structured** copy of each finding lives in Airtable (`Findings` table):
> rank, status, depth, type, innocent explanation, evidence path. This section carries the
> *reasoning* — why it's deep vs shallow, why it stings, what was ruled out. Don't duplicate
> the fields here; they will drift.

**Rank 1 — RESOLVED, do not reuse — two of three Life Planner order buttons routed to a test-SKU checkout**
Depth: was DEEP · Type: broken checkout SKU
Innocent explanation: a test link that never got swapped out when the page went live.
Why it matters (historical): two of three "order" buttons on the Life Planner sales page routed to a live Wix checkout showing a test SKU at AED 9.00 instead of the real $30.22 product. Re-walked 2026-07-20: all three buttons now route to real Stripe checkout links and the old test-SKU page 404s. No longer an open finding.
Evidence: none promoted yet

**Rank 2 — RESOLVED (header instance only) — header logo linked to an orphaned duplicate site**
Depth: was DEEP (header) · Type: broken primary-navigation link
Innocent explanation: likely a leftover rebuild link, just missed on the second element when the header one got fixed.
Why it matters (historical): the header logo now correctly links home — fixed. The footer instance of the same defect is tracked fresh as Rank 4 below, since it's a distinct, still-live element.
Evidence: none promoted yet

**Rank 3 — UNUSED — contact page email link doesn't match its mailto target**
Depth: SHALLOW · Type: contact-info mismatch
Innocent explanation: an old alias that probably never got updated when she switched to replying from her personal inbound address.
Why it matters: the contact page's displayed email address doesn't match its mailto target — a message sent to the address she shows visibly goes to a different inbox than the one she's actually replying from. This is currently the strongest open finding per the raw walk notes.
Evidence: none promoted yet

**Rank 4 — UNUSED, confirmed 2026-07-20 — footer logo still links to the orphaned duplicate site** *(RESERVED — call bait, never emailed)*
Depth: SHALLOW · Type: broken secondary-navigation link
Innocent explanation: likely the same leftover rebuild link, just missed on the second element when the header one got fixed.
Why it matters: the site's footer logo (present on every homepage view and on /blank itself, distinct from the header logo already fixed) still links to https://www.avneetkohli.com/blank, the same orphaned old-design duplicate. The Loom skeleton drafted for the two open findings together: Show — the footer logo at the bottom of https://www.avneetkohli.com/ (still pointing to /blank) and the contact page's email link at https://www.avneetkohli.com/contact (still mismatched); Fix — point the footer logo home the same way the header logo already got fixed; make the visible contact email match its mailto target; Done state — every logo on the site, header and footer, goes home, and the contact email link goes where it visibly says it goes.
Evidence: none promoted yet

## SMYKM Hook

`Her show "Forward with Avneet Kohli" just ran an episode with Meeta Gupta (Moolah) unpacking the money blindspots that quietly shape founders' decisions` — **WORK** — source: https://www.linkedin.com/posts/avneet-kohli_some-of-the-biggest-financial-challenges-activity-7481321066058141697-70Pp

---

*Email history lives in Airtable (`Touches` table) — every send and reply, verbatim.
Price discovery answer and anchor live on the Airtable `Leads` record.
Neither is duplicated here.*
