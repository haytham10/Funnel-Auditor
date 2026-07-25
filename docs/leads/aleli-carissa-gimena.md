# Aleli Carissa Gimena

<!-- airtable-record: TBD -->
> **Site:** https://www.alelicarissa.com/awakening-coaching-program · **Profile:** https://www.instagram.com/empowermentlifecoachingonline, https://www.youtube.com/@empowermentlifecoachingonline
> **Walked:** 2026-07-17 · **Slug:** `aleli-carissa-gimena`

---

## Overview

Aleli Carissa Gimena runs Empowerment Life Coaching, a solo spiritual/mindset coaching practice ("Intuitive Success Mentor," IPHM-accredited) based in Dubai. Site is Kajabi-hosted (alelicarissa.com) with a Stripe subscription checkout and a Calendly discovery-call booking. Main offer is the 1-on-1 Spiritual Awakening / Holistic Therapy & Soul Coaching program on a paid ladder ($444/mo installment, $1,111/mo accelerated, $5,555 pay-in-full elite), plus higher-tier group containers (Soulful CEO MasterMind, Divine Goddess Creatrix, Reiki/Life-Coaching Certification). Audience ~2,600 IG (@empowermentlifecoachingonline) plus a ~22K YouTube channel. Own face, own story, replies as herself.

## Funnel Walk

- Stop 1 (Entry) — the awakening-coaching-program page is one long Kajabi sales page; links mostly repeat the same offer/checkout. Minor: no single "Start Here," but not a felt cost.
- Stop 2 (Freebie) — no standalone freebie/opt-in in the crawled funnel; a newsletter (bit.ly/elc-mail) is referenced in copy. Email capture (Kajabi) is present. Not a Lane 1 leak.
- Stop 3 (Offer/Sales) — clear paid ladder with prices shown ($444/$1,111/$5,555). BUT the promo banner at the pricing block still reads "AVAILABLE until 2/2/2026, use GIFT10 for 10% OFF" — 167 days past.
- Stop 4 (Checkout/Booking) — Stripe $444/mo subscription checkout renders and works. The real Calendly (calendly.com/alelicarissa/discovery) works, open July 2026 slots. BUT the in-copy discovery-call link on her sales page resolves to www.alelicarissa.com/calendly.com/alelicarissa/discovery → hard 404 ("Page not found") on her own domain (missing https:// = Kajabi treated it as a relative path).
- Stop 5 (Audience ownership) — owns a Kajabi list + newsletter; also drives to WhatsApp (+971525234237 UAE). Not fully rented. No leak.

## Evidence

- **Site vision pass:** `VISION PASS: COMPLETE — 16 of 16 required images confirmed read`
- **Pasted evidence:** none — crawl-only walk (Playwright fallback; Firecrawl MCP tools not exposed this session).
- **Screenshots:** none promoted yet — see per-finding notes below. Independent verification: VERIFIED — broken discovery-call link confirmed on pages/1_alelicarissa-com-awakening-coaching-program.txt (authored as bare calendly.com/alelicarissa/discovery) + www.alelicarissa.com/calendly.com/alelicarissa/discovery screenshot 'Page not found' + live HEAD/GET 404 (real calendly.com/alelicarissa/discovery = 200). Email RESOLVED 2026-07-19 → hello@empowermentlifecoaching.online (found on her YouTube + Facebook about pages), email-verify PASS (deliverable, role account, only address available); Email Verified checked → PROMOTED to Audit Ready. 3 machine flags rejected in the vision pass: price_mismatch (Kajabi's OWN plan pricing page $216/$431 vs $179 checkout, not her offer), coming-soon (Kajabi platform copy), kajabi-404 (app.kajabi.com/learn platform link, not her funnel).

## Gates

- **Gate 0:** Pass — UAE/Dubai confirmed (prior qualify: Noomii + ae.linkedin; UAE WhatsApp listed); funnel floor confirmed (real reachable paid ladder, working Stripe checkout + Calendly); activity within 30 days (prior qualify: IG 14 Jul 2026); audience 2,600 IG (+~22K YouTube).
- **Gate 1:** Pass — solo operator; own name, face, and story; replies as herself; no team/agency/gatekeeper.
- **Lane:** Lane 1 (felt leak) — a provably broken primary conversion click on a committed operator.

## Findings — reasoning

> The **canonical, structured** copy of each finding lives in Airtable (`Findings` table):
> rank, status, depth, type, innocent explanation, evidence path. This section carries the
> *reasoning* — why it's deep vs shallow, why it stings, what was ruled out. Don't duplicate
> the fields here; they will drift.

**Rank 1 — "book your 1-on-1 discovery call" link in the Awakening program page dead-ends on her own domain**
Depth: DEEP · Type: broken link on the primary conversion click
Innocent explanation: the link was typed without the https:// prefix, so Kajabi resolved it as a page on her own domain instead of Calendly — a one-character fix, not a rebuild.
Why it matters: this is the exact click a ready buyer makes to reach her, live-verified as dead (HEAD 404 + GET 404; the real Calendly returns 200). It is not a peripheral element — it's the highest-intent CTA on her flagship sales page. The Loom skeleton drafted for this finding: Show — the Awakening program page, the in-copy "book your 1-on-1 chat with me at calendly.com/alelicarissa/discovery" link, clicking it → "Page not found" on her own domain; Fix — in Kajabi, edit that text link's URL to the full https://calendly.com/alelicarissa/discovery (make it an absolute link so it stops resolving as a page on her own site); Done state — clicking "book your discovery call" opens her live Calendly with open July slots, instead of a 404.
Evidence: none promoted yet

**Rank 2 — promo banner at the pricing block still reads a February deadline** *(RESERVED — call bait, never emailed)*
Depth: SHALLOW · Type: stale urgency copy
Innocent explanation: the deadline banner is leftover from the last enrollment round and was never refreshed.
Why it matters: reads "AVAILABLE until 2/2/2026, use GIFT10 for 10% off" — five months past at walk time — so a buyer reading the price assumes the offer (and the discount) already closed and closes the tab.
Evidence: none promoted yet

## SMYKM Hook

`"Desire Everything, Need Nothing" — the theme of your Monday community call — is the cleanest way I've seen to name the detachment piece most manifestation work skips over.` — **WORK** — source: https://www.instagram.com/p/Da8wXV0AoUe/

---

*Email history lives in Airtable (`Touches` table) — every send and reply, verbatim.
Price discovery answer and anchor live on the Airtable `Leads` record.
Neither is duplicated here.*
