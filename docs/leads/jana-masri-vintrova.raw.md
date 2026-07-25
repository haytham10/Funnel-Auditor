<!--
VERBATIM ARCHIVE — DO NOT EDIT
Source: Notion page 39e382c8-4585-816a-9e76-e3308e36a328
Fetched: 2026-07-25T13:40:25Z
This is the unparsed original. The structured copy lives in Airtable
(Touches / Leads). If a parse is ever wrong, this is the source of truth.
-->

## Overview
Jana Masri Vintrova, founder of GOREAL, Dubai-based licensed Behavioral Nutritionist and ICF ACC-certified Life Coach (10+ years, Precision Nutrition L1/L2, MBIT, psychology degree, UAE DED licensed). Runs a Kartra-built funnel at [go-real.co/janamasri](http://go-real.co/janamasri): two lead-magnet e-books, a 3-tier monthly 1-on-1 coaching subscription (Lite \$150 / Standard \$250 / Premium \$500 USD), a standalone 8-week "Discover Your Food Intolerances" paid program (\$197), and a live booking calendar for a free 15-min consult. Also running a newer, separate single-offer brand ("Wunderbar," 2,200 AED/month, 2026 copyright) not yet linked from her main Linktree hub — likely an in-progress rebrand/repositioning, not confirmed.
## Funnel Walk
Stop 1 (Entry — homepage): Clean single narrative (hero → freebie → coaching offer → second freebie → contact/calendar). Site-wide "contact" mail icon (in the nav/footer, reproduced identically on /services and /janamasri-calendar — a shared template block) links to a dead Kartra page. See Lane + Finding.
Stop 2 (Freebie): Two working freebie e-books ("Ultimate Guide to Nutrition," "Flat Belly Anti-Bloating Guide") — both capture first/last name, email, and phone before delivering. Clean.
Stop 3 (Offer/Sales — /services): Three clearly-priced monthly coaching tiers, no genuine contradiction. Machine flagged a Tier A "price mismatch" against the separate program's own checkout (\$197) — rejected on manual read, different products (see Evidence).
Stop 4 (Checkout — /discover-your-food-intolerances): Live, working USD 197 cart with billing/payment fields. Clean.
Stop 5 (Audience ownership): Owns email capture via 2 working freebies; active across LinkedIn, Instagram, YouTube, TikTok via a shared Linktree hub. Not fully rented.
## Evidence
- Site vision pass: VISION PASS: COMPLETE — 8 of 8 required images confirmed read
- Pasted evidence: none attached — Notion page body was blank on fetch; crawl-only walk.
- Machine flags rejected in the vision pass: 1 — unrelated products (the packet's Tier A "price_mismatch" flag compared the coaching-subscription tiers (\$150/\$250/\$500) against a completely separate one-time 8-week program's own checkout (\$197) — two different SKUs, not the same product priced two ways).
## Gates
Gate 0: Pass — UAE-based confirmed (About page, LinkedIn location, UAE DED license, WhatsApp +971 number, listed on 4+ independent Dubai directories: Fresha, [healthfinder.ae](http://healthfinder.ae), magicpin, therapr). Funnel confirmed (2 working freebies, tiered coaching offer, live \$197 checkout, live booking calendar). Audience confirmed: LinkedIn 5,308 followers (apimaestro li-profile, 2026-07-16), above the 1,500 floor. 30-day activity confirmed via the same multi-platform presence and the freshly-built second brand ("Wunderbar," 2026 copyright, AED-native pricing) showing live, recent business development.
Gate 1: Pass — solo operator. First-person "About Me" throughout, no team/agency language anywhere, single named practitioner, direct WhatsApp/personal contact.
## Lane + Finding
Lane 1 — OPEN. One felt leak survives both filters (sting + vitamin).
Finding: the "contact" mail icon in her site's nav/footer — present identically on the homepage, /services, and /janamasri-calendar (a shared template block, so almost certainly every page) — routes to a Kartra page reading "Something went wrong! The page you were looking for does not exist." Confirmed live via direct curl (HEAD and GET, both 404), independent of the crawl and the screenshot.
Innocent explanation: the linked Kartra page/asset was likely deleted or unpublished during a recent site edit — she's clearly been rebuilding (a second brand, Wunderbar, just went live) — and that one icon link never got repointed.
## Findings Bank
1. Site-wide "contact" mail icon (nav/footer, every page) links to a dead Kartra page ("Something went wrong! The page you were looking for does not exist") — confirmed live via curl, independent of the crawl — innocent: the linked page was likely removed/unpublished during a recent site rebuild and the icon link never got updated.
(Only one finding survived both filters. Other machine flags either resolved clean on manual read — the freebie forms are legitimate opt-ins, the coaching-tier pricing is consistent, the booking calendar has real July 2026 availability — or were rejected as false positives (see Evidence), or stayed unverified without visual confirmation (two Kartra checkout-popup buttons on /services that Firecrawl/cta-probe couldn't click-resolve; no evidence either way, so not banked).)
## Loom Skeleton
- Show: the "contact" mail icon (small circular icon, blue background, nav/footer) on [https://www.go-real.co/janamasri](https://www.go-real.co/janamasri) — click it live on screen to land on the "Something went wrong!" Kartra error page.
- Fix: in Kartra's page/site builder, edit that icon's link target — point it to a live page, or simply swap it to a mailto: link or the same WhatsApp destination already used elsewhere on the page, instead of the orphaned Kartra asset ID.
- Done state: clicking the mail icon anywhere on the site opens a real contact method (a working page, or a direct email/WhatsApp action) instead of an error page.
## SMYKM Hook
SMYKM hook: her About Me on the new Wunderbar site — she once crossed 650 km of desert by camelback and holds a government-issued Dubai camel riding and racing license — LIFE — source: [https://www.wunderbar.ae/](https://www.wunderbar.ae/)
## Email Thread Log
\[2026-07-17\] — Touch #1 — Subject: "the camel racing license" — Sent
Hey Jana
Crossing 650 km of desert on a camel, then getting the government to
license you for it, is not something most nutrition coaches have on their
bio page.
I went to your site after that and tried the contact icon in the footer. It
leads to a dead Kartra page, the one that says something went wrong.
Same icon sits on every page, so anyone who wants to reach you outside a
booking form hits that same wall first.
Is that link just waiting on a fix, or did the page behind it get taken
down on purpose?
Haytham
Reply: No reply
Next: Touch 2 due 2026-07-20
## Price Discovery
