# Coach G

<!-- airtable-record: TBD -->
> **Site:** https://coach-g.com/ · **Profile:** none found
> **Walked:** 2026-07-15 · **Slug:** `coach-g`

---

## Overview

Coach G (male; solo personal brand, "Gloria" a partner/support figure per the About menu) — transformational life / mindset coach in Dubai Marina (Al Murjan Tower, Al Marsa Street). WordPress + Elementor + WooCommerce. Sells the proprietary R.I.S.E. Method (Reveal, Integrate, Shift, Embody) as a tiered coaching ladder from AED 1,000 (Breakthrough, 1x90min) to AED 3,800 (Fast Track) up to ~AED 10,200. SEO/ads-led: 200+ blog articles, ranks for "best life coach in Dubai," claims 500+ clients over 15 years, runs a 15-quiz assessment engine ("120K+ tests taken"). Front door is a free 30-min Calendly discovery call.

## Funnel Walk

- Stop 1 (Bio/Home) — dark video-hero homepage, 10-item nav, primary CTA "Book Your Free Assessment" to a free discovery call. Clear entry.
- Stop 2 (Freebie) — "Primed for Success" ebook delivered as a raw ungated PDF (direct /wp-content/ download, HTTP 200 application/pdf, "No credit card required. Instant access.") — no opt-in gate on the lead magnet.
- Stop 3 (Offer/Sales) — R.I.S.E. sales page + Pricing; live WooCommerce products AED 1,000 / AED 3,800 up to ~AED 10,200. Polished, complete, priced; full Reveal/Integrate/Shift/Embody copy rendered.
- Stop 4 (Checkout) — live WooCommerce: add-to-cart 15131 loads "Breakthrough Coaching Session" 1.000,00 AED, cart totals, coupon field, Proceed to Checkout (Stripe), card logos. Works cleanly desktop + mobile.
- Stop 5 (Audience ownership) — homepage DOES carry a working newsletter opt-in ("Monthly insights...", email input + Subscribe), but it posts to a Formspree inbox relay (formspree.io/f/xgooaqlo), not an ESP/list. Quizzes (15, "120K+ tests taken") route results to WhatsApp with no visible email gate. Owned-list capture is thin: a form that emails him each address rather than building a nurturable list.

## Evidence

- **Site vision pass:** `VISION PASS: COMPLETE — 11 of 11 required images confirmed read`
- **Pasted evidence:** none — crawl-only walk (Firecrawl MCP unavailable this session; fetched via Playwright with an extended wait to clear a Cloudflare JS challenge).
- **Screenshots:** none promoted yet — see per-finding notes below

## Gates

- **Gate 0:** Pass — UAE base confirmed (Al Murjan Tower, Al Marsa Street, Dubai Marina; +971 58 554 1780; footer on every page). Funnel live (WooCommerce + Stripe + Calendly HTTP 200). Activity: maintained ads/SEO operation (latest blog 2026-06-28 per prior confirm). Audience: no hard follower count obtainable (no Apify spent on this re-confirm run) — cleared qualitatively at the same bar: 15-quiz engine "120K+ tests taken," 200+ blog articles, active FB/YouTube/X, 500+ clients / 15 yrs.
- **Gate 1:** Pass — solo operator: self-authored R.I.S.E. method ("I created this method to help individuals, couples, high-performers"), single personal brand, 15-yr origin story. "About Gloria" reads as a partner/support figure, not a gatekeeper.
- **Lane:** Lane 2 (no leak) — everything visible works and is professionally built; nothing broken survived the vision pass.

## Findings — reasoning

No Lane 1 finding was banked for this lead — the Findings Bank is empty. Not applicable in the sense of a broken/felt-cost leak; the walk instead surfaced a mechanism-level warm-up angle, kept below, that does not clear the sting test for a cold send.

Ruled out in the vision pass: four machine flags were rejected — checkout "no-payment-form" (the cart renders fine with a live Proceed-to-Checkout + card logos; the payment form is the next step); a blank Calendly widget (calendly.com/coach-g-dubai/30min returns HTTP 200 live, blank is an async-embed capture artifact); "no-email-capture-anywhere" (the homepage newsletter opt-in IS present and functional via Formspree — flag is a misfire); pricing-tables-blank (lazy-load/static-capture artifact; homepage shows real prices, cart is live).

**Warm-up angle (not a Lane 1 finding, not for cold send)**
An ads/SEO-led operator with a large quiz traffic engine (15 quizzes, 120K+ tests taken) and an ungated raw-PDF lead magnet, whose only email capture is a homepage newsletter box wired to a Formspree inbox relay rather than an owned list/ESP — paying to attract an audience it isn't capturing to a list it can nurture. This is mechanism-level (best practice), not a broken painkiller — held, not cold-sendable. Note: a prior walk's read of "zero email capture anywhere" was inaccurate; capture exists, it's just relayed to an inbox, not a list.

## SMYKM Hook

`not run yet — see haytham-hook-finder`

---

*Email history lives in Airtable (`Touches` table) — every send and reply, verbatim.
Price discovery answer and anchor live on the Airtable `Leads` record.
Neither is duplicated here.*
