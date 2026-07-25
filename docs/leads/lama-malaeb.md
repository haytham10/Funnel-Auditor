# Lama Malaeb

<!-- airtable-record: TBD -->
> **Site:** https://www.lamamalaeb.com/ · **Profile:** https://www.skool.com/@lama-malaeb-7368
> **Walked:** 2026-07-13 · **Slug:** `lama-malaeb`

---

## Overview

Lama Malaeb is Dubai's bilingual (Arabic + English) AI coach and corporate trainer, founder of AI Growth Hub and an official HeyGen Ambassador. She sells two-day corporate AI workshops (AED 18,400), day rates (AED 6,000), GCC delivery (AED 7,500) and coaching retainers (AED 11,000) to SMEs, entrepreneurs and L&D teams across the UAE, Saudi Arabia and the GCC. Funnel runs on Squarespace: home → free "AI Readiness Quiz" (opt-in capturing name + WhatsApp + email) → discovery call / corporate workshop via a contact form, plus a nas.io community (AI Growth Hub). Audience ~3.4K on Instagram (@lamamalaeb.co), ~800 on her weekly email list, plus a small Skool community.

## Funnel Walk

- Stop 1 (Bio / home) — Clean, dense landing: hero, testimonial, 4-step method, services, FAQ accordion, 3-option pricing CTA. Multiple opt-in points. Strong.
- Stop 2 (Freebie — /ai-quiz) — Interactive 8-question "AI Readiness Quiz"; capture screen takes first name + WhatsApp + email + business type + country before results. Results push "Book My Discovery Call" + free community. Real opt-in (a machine "no email capture" flag was a misfire — capture is JS-gated inside the quiz).
- Stop 3 (Offer — home pricing) — Prices visible on-page (AED 18,400 / 6,000 / 7,500 / 11,000). No instant checkout or booking: Option A = "DM WORKSHOP on LinkedIn or email hello@lamamalaeb.com"; Option B = join nas.io; Option C = "Contact me" form.
- Stop 4 (Checkout — /cart) — Squarespace commerce is enabled but the cart is empty ("You have nothing in your shopping cart") — no products sold through it; all offers route to a form/DM. Not a break, just a dormant store.
- Stop 5 (FAQ) — Homepage FAQ accordion (5 questions) ends with a "See All FAQs" button which links to /FAQ, returning HTTP 404. The real FAQ page is published at /faqs (200, correctly linked from the top nav). See Findings.

## Evidence

- **Site vision pass:** `VISION PASS: COMPLETE — 7 of 7 required images confirmed read`
- **Pasted evidence:** none — crawl-only walk
- **Screenshots:** none promoted yet — see per-finding notes below

## Gates

- **Gate 0:** Pass — UAE base confirmed (Dubai, stated on-site + LinkedIn/IG); funnel present (quiz opt-in + priced workshop offer); activity within 30 days (Skool active ~8d ago, active LinkedIn posting, 268 IG posts); audience 1,500+ (~3.4K IG @lamamalaeb.co).
- **Gate 1:** Pass — Solo operator. She is the individual coach/founder; every offer routes to her directly ("DM me / email hello@ / Contact me"). No team gatekeeper.
- **Lane:** Lane 1 (felt leak) — a dead link on the path to a high-ticket buy.

## Findings — reasoning

**Rank 1 — "See All FAQs" button 404s right before a high-ticket decision**
Depth: not explicitly labeled; reads DEEP — it sits at the objection-handling step directly before an AED 18,400 workshop decision.
Type: dead link (stale button pointing at an old page slug)
Innocent explanation: the FAQ page was published/re-slugged as /faqs (correctly wired into the top nav), but the homepage "See All FAQs" button still points at the old /FAQ slug and was never repointed — a stale button link after an edit, not neglect.
Why it matters: the homepage FAQ section's "See All FAQs" button links to /FAQ, which 404s — the real FAQ page lives at /faqs. A prospect handling final objections right before an AED 18,400 workshop clicks through and hits a dead end (a soft-404 that dumps them back to a homepage-looking page with no answers).
Loom skeleton (not sent, kept for a walkthrough offer): show the homepage FAQ accordion, click "See All FAQs" to the /FAQ 404 (lamamalaeb.com/FAQ), then the working /faqs page side by side; fix would be editing the "See All FAQs" button's link in Squarespace from /FAQ to /faqs (the existing published page); done state is the button opening the real FAQ page, so a buyer reading FAQs right before a workshop gets their answers instead of a dead end.
Evidence: none promoted yet.

**Rank 2 — no instant booking/checkout for the premium workshop offer** *(UNUSED — reserve finding)*
Depth: not explicitly labeled — structural friction on the highest-ticket offer rather than a broken page.
Type: manual-only conversion path (DM/email required, no self-serve booking)
Innocent explanation: solo operator who prefers to qualify each corporate deal personally before scheduling, so a manual first touch is deliberate rather than an oversight.
Why it matters: the premium workshop offer has no instant booking or checkout: at the pricing section the only next step for a decided corporate buyer is "DM WORKSHOP on LinkedIn or email hello@lamamalaeb.com" — a hot lead has to send a DM/email and wait rather than book a slot on the spot.
Evidence: none promoted yet.

Three machine flags were rejected on the vision pass and not banked: a stale-date flag (blog post publish dates, not an event), a "no-opt-in-on-quiz" flag (capture is JS-gated, confirmed present in the HTML), and a layout-overlap flag (a fixed newsletter popup duplicated by the full-page capture; mobile rendered clean).

## SMYKM Hook

`You built a business without ever filming your own face, and turned that into the Camera-Shy Creator Challenge launching Jul 20` — **WORK** — source: https://www.linkedin.com/posts/lamamalaeb_the-camera-shy-creator-challenge-5-days-activity-7480242366210269184-4NXm (posted Jul 7 2026)

---

*Email history lives in Airtable (`Touches` table) — every send and reply, verbatim.
Price discovery answer and anchor live on the Airtable `Leads` record.
Neither is duplicated here.*
