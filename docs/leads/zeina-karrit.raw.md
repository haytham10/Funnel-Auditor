<!--
VERBATIM ARCHIVE — DO NOT EDIT
Source: Notion page 3a2382c8-4585-8108-9339-cadac968b530
Fetched: 2026-07-25T13:41:28Z
This is the unparsed original. The structured copy lives in Airtable
(Touches / Leads). If a parse is ever wrong, this is the source of truth.
-->

## Overview
Zeina Karrit is a solo career/executive coach and recruiter in Dubai (13+ years GCC hiring, ex-Michael Page), running a one-page Wix funnel at [zeinakarrit.com](http://zeinakarrit.com). She sells a native-AED coaching ladder via Stripe "Buy Now" links: Career Clarity Intensive 2,000 AED, Market Access 4,000, Executive Influence 6,000, Recruiter Network Access 4,000, and an Executive Coaching Retainer 3,500 AED/month (6-month min). Lead-gen runs through two Typeform flows (a "Book a Call" discovery call and a "Stay On My Radar" talent-network signup) plus a Linktree. Audience: \~50,477 LinkedIn followers. Email [contact@zeinakarrit.com](mailto:contact@zeinakarrit.com), phone +971 56 221 4540.
## Funnel Walk
Stop 1 ([zeinakarrit.com](http://zeinakarrit.com) home) — full one-page site: hero, 1:1 coaching section, 5-offer ladder with AED prices, impact stats, About, radar opt-in, single testimonial, FAQ. Clean, on-brand, loads fine desktop + mobile.
Stop 2 (5x Stripe checkouts) — all five "Buy Now" links live (HTTP 200), prices match the site exactly (AED 2,000 / 4,000 / 6,000 / 4,000 / 3,500-mo). BUT every checkout opens under merchant name "Unicorn Talent," not Zeina Karrit — see Finding.
Stop 3 (Book a Call — Typeform Wl7115ao) — live, "free 15-minute discovery call," clean.
Stop 4 (Stay On My Radar — Typeform TtlP9h3D) — live, but it is a "Join My Talent Network" candidate-placement form ("I can better match you to exciting roles"), i.e. her recruiting side, not the coaching offer.
Stop 5 (Linktree /zkarrit) — live, 4 links (hire-talent, discovery call, talent network, LinkedIn), WhatsApp + Email contacts.
## Evidence
- Site vision pass: VISION PASS: COMPLETE — 10 of 10 required images confirmed read
- Pasted evidence: none — crawl-only walk.
- Machine flags rejected in the vision pass: 1 — Stripe checkouts defaulted to USD display / "United States" billing country, but this is a US-scraping-proxy artifact (Firecrawl fetched from a US IP; Stripe picks default currency/country by visitor IP), NOT what a Dubai visitor sees — rejected, not treated as a finding.
Finding evidence paths:
- #1 checkout brand mismatch: evidence/zeina-karrit/screenshots/buy_stripe_com_aFa00ja4Z6ADbKD4cncMM0d_desktop.png, buy_stripe_com_00wfZh6SNf793e7dMXcMM0c_desktop.png, buy_stripe_com_3cI6oHa4ZbUX4ibfV5cMM0b_desktop.png, buy_stripe_com_00w28rfpjcZ1eWP10bcMM09_desktop.png, buy_stripe_com_7sY6oH90VaQTeWP6kvcMM0a_desktop.png (all show "Unicorn Talent" logo + "Pay securely at Unicorn Talent" / "authorize Unicorn Talent to charge you"); contrast evidence/zeina-karrit/screenshots/www_zeinakarrit_com_desktop.png ("Zeina Karrit" branding throughout).
- #2 thin social proof: evidence/zeina-karrit/screenshots/www_zeinakarrit_com_desktop.png (TESTIMONIALS section = one quote; SNAPSHOT OF MY IMPACT = "1000+ Careers Transformed", "90% Client Success Rate"); evidence/zeina-karrit/pages/1_zeinakarrit-com.txt and evidence/zeina-karrit/_firecrawl_raw/1.html (testimonial count = 1).
- #3 hero CTA misdirection: evidence/zeina-karrit/screenshots/www_zeinakarrit_com_desktop.png (hero "Stay On My Radar" primary button) + evidence/zeina-karrit/screenshots/form_typeform_com_to_TtlP9h3D_desktop.png ("Join My Talent Network" candidate form).
Independent verification: VERIFIED — bank #1 checkout merchant-name mismatch confirmed on evidence/zeina-karrit/screenshots/buy_stripe_com_00wfZh6SNf793e7dMXcMM0c_desktop.png ("Pay securely at Unicorn Talent" + unicorn logo, live AED 4,000 Market Access Program) vs www_zeinakarrit_com_desktop.png (Zeina Karrit branding throughout, no on-site mention of Unicorn Talent). All 5 desktop checkouts carry the Unicorn Talent logo; genuine live checkouts, not error/placeholder; USD display disregarded as US-proxy artifact.
## Gates
Gate 0: Pass — UAE base confirmed (Dubai; +971 phone, GCC-only copy), funnel real (5 live Stripe checkouts, prices reachable), 30-day activity (LI post \~2d ago per pre-flight), audience 50,477 LI.
Gate 1: Pass — solo operator throughout: own face/name in hero, About, testimonial and Linktree; first-person voice ("I am Zeina Karrit"); no "we"/agency/support-desk. Payments run through her own company entity (Unicorn Talent), which is the finding, not a gatekeeper.
## Lane + Finding
- Lane 1: Felt leak — a real, point-of-payment trust gap on an otherwise clean funnel.
- Finding (bank #1): Every "Buy Now" button sends the buyer to a Stripe checkout branded "Unicorn Talent" (logo + "Pay securely at Unicorn Talent"), with nothing on [zeinakarrit.com](http://zeinakarrit.com) connecting that name to Zeina — an unfamiliar company appears at the exact moment a personal-brand buyer commits 2,000-6,000 AED, and it is the name that will hit their card statement.
- Innocent explanation: Unicorn Talent is almost certainly her licensed UAE company / Stripe trade name (a UAE Stripe account bills under the registered entity), and she simply never added a one-line reassurance tying it to her name — a 5-minute fix, not a real disconnect.
## Findings Bank
1. Every "Buy Now" checkout opens under merchant "Unicorn Talent," not Zeina Karrit, with no on-site explanation — an unfamiliar name (and card-statement descriptor) at the moment of payment on 2,000-6,000 AED offers — innocent: Unicorn Talent is her licensed company / Stripe entity and she never added a reassurance line.
2. The "TESTIMONIALS" section carries exactly one anonymous quote ("Chief Operations Officer – Chemicals, KSA") while the page claims "1000+ Careers Transformed" and a "90% Client Success Rate" — thin proof for premium offers, the numbers outrun the evidence — innocent: she has the results but hasn't collected/published named client quotes yet.
3. The hero's most prominent CTA, "Stay On My Radar," routes to a free "Join My Talent Network" candidate-placement form (her recruiting side), not the paid coaching ladder — top-of-page attention is spent collecting job-seeker leads instead of selling programs — innocent: the radar form serves her recruiting business and she reuses it as the site's catch-all CTA.
## Loom Skeleton
- Show: [zeinakarrit.com](http://zeinakarrit.com) hero → click a "Buy Now" (e.g. Career Clarity 2,000 AED) → the Stripe page reading "Unicorn Talent" / "Pay securely at Unicorn Talent."
- Fix: in Wix/Stripe, add a one-line reassurance under each Buy Now ("Payments are processed securely by Unicorn Talent, my company") or set the Stripe public business name / statement descriptor to "Zeina Karrit."
- Done state: a buyer who clicks Buy Now sees a name they recognize (or an explicit "that's me") and completes the payment without the "wait, who is this?" pause.
## SMYKM Hook
SMYKM hook: Loved your line this week that career coaching isn't an AI tool or CV writing — it's presence, belief in someone's potential, and expertise — WORK — source: [https://www.linkedin.com/posts/zeina-karrit_best-feedback-i-got-last-week-this-is-what-activity-7484819385635860480-dO9N](https://www.linkedin.com/posts/zeina-karrit_best-feedback-i-got-last-week-this-is-what-activity-7484819385635860480-dO9N)
## Email Thread Log
\[2026-07-21\] — Touch #1 — Subject: "not an AI tool" — Sent
Cold opener sent via Inbox 2, opening on the SMYKM hook and the Lane 1 finding (bank #1) per the row's Notes.
Reply: No reply
Next: 2026-07-24 — cold Touch 2 due (must carry the next unused Findings Bank entry, the Loom offer, or a disambiguating question — never a bare bump)
## Price Discovery
