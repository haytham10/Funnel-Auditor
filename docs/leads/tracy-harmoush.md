# Tracy Harmoush

<!-- airtable-record: TBD -->
> **Site:** https://playbookapp.io/creators/tracy-harmoush-app-1 · **Profile:** https://www.instagram.com/tracyharmoush
> **Walked:** 2026-07-20 · **Slug:** `tracy-harmoush`

---

## Overview

Tracy Harmoush (Tracy Harmoush Ariss) — Dubai-based fitness personality and calisthenics/mobility instructor, 692K IG followers, Arab Woman's Award 2020 (UAE, community impact in fitness). Main funnel: her own creator page on Playbook (a fitness-creator SaaS), selling "LIVE With Tracy" — a workout/nutrition app subscription, $14.99/month or $99.99/year with a 7-day free trial, promoted site-wide as "Start today for only $1." She also runs a separate branded storefront (un-traceable.com, Shopify) for her "Untraceable" app/apparel brand. Solo operator — own face, own story, own support inbox, no agency/team layer visible.

## Funnel Walk

- Stop 1 (Bio/entry, playbookapp.io/creators/tracy-harmoush-app-1) — 5 near-equal "Start today for only $1" CTAs, no single primary next step, but not broken — funnels toward the one checkout either way.
- Stop 3 (Offer/sales, same entry page) — the page's own FAQ ("How much does the app cost?") states plainly: "You can join my app and community FREE for the first 7 days. After that, you'll pay $14.99/month or $99.99/year" — directly contradicting the 12 "$1" CTAs on the same page. No $1 price exists anywhere past the hero button.
- Stop 4 (Checkout, my.playbookapp.io/tracy-harmoush/checkout?promo=tracy1&sourceUrl=livewithtracy.app) — reached FROM her own promoted link with her own promo code (`tracy1`) auto-filled in the field — the checkout shows "Coupon not found" in red, no $1 price anywhere, and confirms "$0.00 for 7 days; converts to $99.99 annually renewing subscription." A visitor who followed her own "$1" link hits a broken discount code and a different price entirely.
- Stop 1 (footer/opt-in) — the newsletter signup's "terms and conditions" link (/terms-conditions-newsletter) is a genuine 404, confirmed live (independently re-fetched, not just screenshot).
- Stop 5 (Audience ownership) — email capture present (newsletter opt-in + per-program signup forms) — she does own a list-building mechanism, not a Stop 5 leak.

## Evidence

- **Site vision pass:** `VISION PASS: COMPLETE — 8 of 8 required images confirmed read`
- **Pasted evidence:** none — crawl-only walk.
- **Screenshots:** none promoted yet — see per-finding notes below. Zero machine flags rejected in the vision pass — the packet's Tier A price-mismatch and dead-link flags both visually + independently confirmed. Independent verification: VERIFIED — the "$1" trial promise never honored at checkout (promo "tracy1" shows "Coupon not found," pricing $99.99/yr or $14.99/mo after 7-day free trial, no $1 anywhere), cross-checked against the entry page's 12x "Start today for only $1" CTAs and the manifest's funnel_links (the CTA href itself is the checkout URL carrying `promo=tracy1`, confirming tracy1 is her own site-embedded auto-applied code, not a guess).

## Gates

- **Gate 0:** Pass — UAE base (Dubai residency, Arab Woman Award 2020 UAE), funnel confirmed live and reachable (checkout loads, real Stripe-style flow), activity confirmed (live site, active promo), audience 692K IG (search-snippet cross-check independent of the walk, matches her own Playbook bio and a Grazia Magazine feature on this exact app launch).
- **Gate 1:** Pass — solo operator, own face/story throughout, own support inbox (support@playbookapp.io is Playbook platform support, not a gatekeeper/agency layer over Tracy herself), no "we"/team copy.
- **Lane:** Lane 1 (felt leak) — real UAE solo operator, real paid funnel, provable pricing/checkout defect.

## Findings — reasoning

> The **canonical, structured** copy of each finding lives in Airtable (`Findings` table):
> rank, status, depth, type, innocent explanation, evidence path. This section carries the
> *reasoning* — why it's deep vs shallow, why it stings, what was ruled out. Don't duplicate
> the fields here; they will drift.

**Rank 1 — newsletter's "terms and conditions" link 404s**
Depth: SHALLOW · Type: broken legal-page link
Innocent explanation: a renamed/removed legal page whose link was never updated.
Why it matters: the newsletter opt-in's "terms and conditions" link (playbookapp.io/terms-conditions-newsletter) is a genuine 404, independently re-fetched and confirmed live — not just a screenshot artifact. Anyone who reads the fine print before signing up hits a dead page. This was the finding actually spent in cold outreach (touch 1); the deeper checkout defect below was held back rather than emailed.
Evidence: none promoted yet

**Rank 2 — site-wide "$1" trial promise never honored at checkout** *(RESERVED — call bait, never emailed)*
Depth: DEEP · Type: pricing/promo-code mismatch at point of payment
Innocent explanation: the promo code was likely set up once on the Playbook backend and either expired or was never wired to the storefront's live pricing copy — an integration slip between the marketing page and Playbook's checkout, not a deliberate bait-and-switch.
Why it matters: this is the strongest verified finding on the funnel — the site-wide "$1" trial promise (12 instances) never appears at checkout. Instead her own auto-applied promo code ("tracy1") returns "Coupon not found," and the real offer converts to $99.99/year (or $14.99/month) after a free 7 days. Every click through her own headline CTA lands on a broken discount and a different price than advertised — a live, revenue-facing defect on the highest-intent page in the funnel, reserved as call bait rather than spent in a cold email. Show: playbookapp.io/creators/tracy-harmoush-app-1 hero CTA ("Start today for only $1") clicked straight through to my.playbookapp.io/tracy-harmoush/checkout?promo=tracy1 — the red "Coupon not found" under the promo field. Fix: get Playbook support to re-link/re-activate the "$1" promo code (or update all site CTAs to match the real 7-day-free / $99.99-$14.99 pricing so the two never disagree again). Done state: clicking "$1" from any of the 5 landing sections lands on a checkout that actually shows $1 (or the CTA copy matches the real trial terms) — no red error, no surprise price.
Evidence: none promoted yet

## SMYKM Hook

`congratulations on the birth of her daughter Leona Gia (born July 17, 2026)` — **LIFE** — source: https://www.instagram.com/p/DbJHdCjNmhg/ (used briefly and warmly per Haytham's explicit call, not elaborated on)

---

*Email history lives in Airtable (`Touches` table) — every send and reply, verbatim.
Price discovery answer and anchor live on the Airtable `Leads` record.
Neither is duplicated here.*
