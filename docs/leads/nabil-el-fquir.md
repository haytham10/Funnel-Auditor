# Nabil El Fquir

<!-- airtable-record: TBD -->
> **Site:** https://jobsearchmastery.me/ · **Profile:** https://jobsearchmastery.me/
> **Walked:** 2026-07-17 · **Slug:** `nabil-el-fquir`

---

## Overview

Nabil El Fquir runs Job Search Mastery (jobsearchmastery.me), a solo executive/career advisory for
senior professionals (Managers, Directors, VPs) targeting UAE & GCC roles. Based in the UAE (Sharjah,
Shams Media City); WordPress + WooCommerce, Stripe/Apple Pay/Tabby checkout, cal.com booking. Paid
ladder: CV & LinkedIn Optimisation (AED 2,899), Job Search Strategy Program (AED 3,799), Executive
Interview Preparation (AED 4,999). Own face, first-person, active recruiter with 20+ years across
MENA. LinkedIn audience 8,008. (No Cap LLC is his own operating entity / separate B2B recruitment
arm — not a gatekeeper on this B2C advisory.)

## Funnel Walk

- Stop 1 (Entry / homepage) — clean hero → single CTA ("Book a Strategy Call") + three package
  cards. Narrows well.
- Stop 2 (Freebie) — four free resources (checklists/framework); each Download button routes to its
  own landing page WITH an email opt-in form (verified live). Captures contacts — not a leak.
- Stop 3 (Offer/Sales) — three service cards, prices clear (AED 2,899 / 3,799 / 4,999), Tabby
  instalments shown. On the flagship AED 4,999 "Executive Interview Preparation" card, the "VIEW
  DETAILS" link points to /offer-conversion-advisory/ which is a hard 404. The other two cards' VIEW
  DETAILS resolve fine; the real detail page for this package lives at
  /executive-interview-preparation/.
- Stop 4 (Checkout/Booking) — WooCommerce checkout works (billing, Country=UAE, Stripe/Apple
  Pay/Tabby, VAT 5%). cal.com booking calendar live with real slots (e.g. Mon 20 Jul: 12:15/1:00/
  1:45pm). No leak.
- Stop 5 (Audience ownership) — email capture present on freebie landing pages; owns a list
  mechanism plus LinkedIn (8,008). Not fully rented. No leak.

## Evidence

- **Site vision pass:** `VISION PASS: COMPLETE — 17 of 17 required images confirmed read`
- **Pasted evidence:** none — crawl-only walk (Playwright fallback; Firecrawl MCP was unavailable at
  walk time).
- **Screenshots:** none promoted yet — see per-finding notes below

Machine flags rejected in the vision pass: 2 — freebie "no email capture" (opt-in form confirmed on
each resource page); cart broken-image thumbnails (unset/lazy-load WooCommerce thumbnails, low felt
cost). Independent verification: VERIFIED — AED 4,999 Executive Interview Preparation card VIEW
DETAILS → /offer-conversion-advisory/ (live 404) vs working /executive-interview-preparation/ (live
200) confirmed on homepage HTML link mapping + curl HEAD/GET of both URLs.

## Gates

- **Gate 0:** Pass — UAE-based confirmed (About: "Executive Career Coach in the UAE", Sharjah/Shams
  Media City); funnel/paid ladder live (AED 2,899-4,999); activity current (og:updated 2026-06-29 +
  active LinkedIn); audience 8,008 > 1,500.
- **Gate 1:** Pass — solo operator: own face, first-person copy, personal cal.com booking,
  single-person About; No Cap LLC is his own entity, not a support/agency wall.
- **Lane:** Lane 1 — a broken detail path on the highest-ticket offer.

## Findings — reasoning

> The **canonical, structured** copy of each finding lives in Airtable (`Findings` table): rank,
> status, depth, type, innocent explanation, evidence path. This section carries the *reasoning* —
> why it's deep vs shallow, why it stings, what was ruled out. Don't duplicate the fields here; they
> will drift.

**Rank 1 — flagship AED 4,999 package's "VIEW DETAILS" link is a hard 404**
Depth: DEEP · Type: broken link on the highest-ticket offer
Innocent explanation: the detail page was re-slugged (offer-conversion-advisory →
executive-interview-preparation) and this one card's link was never repointed — a stale link from a
rename, not a missing offer.
Why it matters: on the homepage offer section, the flagship AED 4,999 "Executive Interview
Preparation" card's "VIEW DETAILS" link points to /offer-conversion-advisory/ and returns a hard 404,
so the highest-intent senior buyer reading up on the most expensive package before paying lands on
"This page doesn't seem to exist." The other two, cheaper cards work fine — this is specifically the
top-tier offer's link that's broken. Used as the Touch 1 opener.
Evidence: none promoted yet — see raw archive (`docs/leads/nabil-el-fquir.raw.md`)

## SMYKM Hook

`Your LinkedIn post this week reframing 'can you help me find a job?' into right person, right
reason, clear relevance, reasonable ask — the cleanest breakdown of why senior networking messages
get ignored that I've read` — **WORK** — source:
[LinkedIn post](https://www.linkedin.com/posts/nabilelfquir_uaejobs-dubaijobs-hiring-activity-7483128480013086721-IJ8S)

---

*Email history lives in Airtable (`Touches` table) — every send and reply, verbatim.
Price discovery answer and anchor live on the Airtable `Leads` record.
Neither is duplicated here.*
