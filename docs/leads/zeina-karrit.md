# Zeina Karrit

<!-- airtable-record: TBD -->
> **Site:** https://www.zeinakarrit.com · **Profile:** https://www.linkedin.com/in/zeina-karrit/
> **Walked:** 2026-07-19 · **Slug:** `zeina-karrit`

---

## Overview

Zeina Karrit is a solo career/executive coach and recruiter in Dubai (13+ years GCC hiring, ex-Michael Page), running a one-page Wix funnel at zeinakarrit.com. She sells a native-AED coaching ladder via Stripe "Buy Now" links: Career Clarity Intensive 2,000 AED, Market Access 4,000, Executive Influence 6,000, Recruiter Network Access 4,000, and an Executive Coaching Retainer 3,500 AED/month (6-month min). Lead-gen runs through two Typeform flows (a "Book a Call" discovery call and a "Stay On My Radar" talent-network signup) plus a Linktree. Audience: ~50,477 LinkedIn followers. Email contact@zeinakarrit.com, phone +971 56 221 4540.

## Funnel Walk

- Stop 1 (zeinakarrit.com home) — full one-page site: hero, 1:1 coaching section, 5-offer ladder with AED prices, impact stats, About, radar opt-in, single testimonial, FAQ. Clean, on-brand, loads fine desktop + mobile.
- Stop 2 (5x Stripe checkouts) — all five "Buy Now" links live (HTTP 200), prices match the site exactly (AED 2,000 / 4,000 / 6,000 / 4,000 / 3,500-mo). But every checkout opens under merchant name "Unicorn Talent," not Zeina Karrit — see Finding.
- Stop 3 (Book a Call — Typeform Wl7115ao) — live, "free 15-minute discovery call," clean.
- Stop 4 (Stay On My Radar — Typeform TtlP9h3D) — live, but it is a "Join My Talent Network" candidate-placement form ("I can better match you to exciting roles"), i.e. her recruiting side, not the coaching offer.
- Stop 5 (Linktree /zkarrit) — live, 4 links (hire-talent, discovery call, talent network, LinkedIn), WhatsApp + Email contacts.

## Evidence

- **Site vision pass:** `VISION PASS: COMPLETE — 10 of 10 required images confirmed read`
- **Pasted evidence:** none — crawl-only walk.
- **Screenshots:** none promoted yet — see per-finding notes below. One machine flag rejected in the vision pass: Stripe checkouts defaulted to USD display / "United States" billing country, but this is a US-scraping-proxy artifact (Firecrawl fetched from a US IP; Stripe picks default currency/country by visitor IP), NOT what a Dubai visitor sees — rejected, not treated as a finding. Independent verification: VERIFIED — bank #1 checkout merchant-name mismatch confirmed (live AED 4,000 Market Access Program checkout reads "Pay securely at Unicorn Talent" + unicorn logo) vs the site itself (Zeina Karrit branding throughout, no on-site mention of Unicorn Talent). All 5 desktop checkouts carry the Unicorn Talent logo; genuine live checkouts, not error/placeholder; the USD display was disregarded as a US-proxy artifact.

## Gates

- **Gate 0:** Pass — UAE base confirmed (Dubai; +971 phone, GCC-only copy), funnel real (5 live Stripe checkouts, prices reachable), 30-day activity (LinkedIn post ~2 days ago per pre-flight), audience 50,477 LinkedIn.
- **Gate 1:** Pass — solo operator throughout: own face/name in hero, About, testimonial and Linktree; first-person voice ("I am Zeina Karrit"); no "we"/agency/support-desk. Payments run through her own company entity (Unicorn Talent), which is the finding, not a gatekeeper.
- **Lane:** Lane 1 (felt leak) — a real, point-of-payment trust gap on an otherwise clean funnel.

## Findings — reasoning

> The **canonical, structured** copy of each finding lives in Airtable (`Findings` table):
> rank, status, depth, type, innocent explanation, evidence path. This section carries the
> *reasoning* — why it's deep vs shallow, why it stings, what was ruled out. Don't duplicate
> the fields here; they will drift.

**Rank 1 — every "Buy Now" checkout opens under merchant "Unicorn Talent," not Zeina Karrit**
Depth: DEEP · Type: brand/trust mismatch at point of payment
Innocent explanation: Unicorn Talent is almost certainly her licensed UAE company / Stripe trade name (a UAE Stripe account bills under the registered entity), and she simply never added a one-line reassurance tying it to her name — a 5-minute fix, not a real disconnect.
Why it matters: every "Buy Now" button sends the buyer to a Stripe checkout branded "Unicorn Talent" (logo + "Pay securely at Unicorn Talent"), with nothing on zeinakarrit.com connecting that name to Zeina — an unfamiliar company appears at the exact moment a personal-brand buyer commits 2,000-6,000 AED, and it is the name that will hit their card statement. Show: zeinakarrit.com hero → click a "Buy Now" (e.g. Career Clarity 2,000 AED) → the Stripe page reading "Unicorn Talent" / "Pay securely at Unicorn Talent." Fix: in Wix/Stripe, add a one-line reassurance under each Buy Now ("Payments are processed securely by Unicorn Talent, my company") or set the Stripe public business name / statement descriptor to "Zeina Karrit." Done state: a buyer who clicks Buy Now sees a name they recognize (or an explicit "that's me") and completes the payment without the "wait, who is this?" pause.
Evidence: none promoted yet

**Rank 2 — testimonials section carries exactly one anonymous quote against claimed "1000+ Careers Transformed"**
Depth: SHALLOW · Type: thin social proof vs. stated claims
Innocent explanation: she has the results but hasn't collected/published named client quotes yet.
Why it matters: the "TESTIMONIALS" section carries exactly one anonymous quote ("Chief Operations Officer – Chemicals, KSA") while the page claims "1000+ Careers Transformed" and a "90% Client Success Rate" — thin proof for premium offers, the numbers outrun the evidence.
Evidence: none promoted yet

**Rank 3 — hero's most prominent CTA routes to a job-seeker form, not the coaching ladder**
Depth: SHALLOW · Type: misdirected primary CTA
Innocent explanation: the radar form serves her recruiting business and she reuses it as the site's catch-all CTA.
Why it matters: the hero's most prominent CTA, "Stay On My Radar," routes to a free "Join My Talent Network" candidate-placement form (her recruiting side), not the paid coaching ladder — top-of-page attention is spent collecting job-seeker leads instead of selling programs.
Evidence: none promoted yet

## SMYKM Hook

`Loved your line this week that career coaching isn't an AI tool or CV writing — it's presence, belief in someone's potential, and expertise` — **WORK** — source: https://www.linkedin.com/posts/zeina-karrit_best-feedback-i-got-last-week-this-is-what-activity-7484819385635860480-dO9N

---

*Email history lives in Airtable (`Touches` table) — every send and reply, verbatim.
Price discovery answer and anchor live on the Airtable `Leads` record.
Neither is duplicated here.*
