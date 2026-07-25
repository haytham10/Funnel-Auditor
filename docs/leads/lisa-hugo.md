# Lisa Hugo

<!-- airtable-record: TBD -->
> **Site:** https://www.lisahugo.com · **Profile:** https://ae.linkedin.com/in/lisa-hugo
> **Walked:** 2026-07-16 · **Slug:** `lisa-hugo`

---

## Overview

Lisa Hugo — Dubai-based executive communication / public speaking coach (Leadership), trading as
Audacia Marketing Management LLC on GoHighLevel (GHL). Author of "Voice of Influence" ($17
front-end book) and host of the "Impact Through Voice" podcast (160,000+ downloads). Offer ladder:
$17 book → two free-masterclass webinar funnels (/iai-webinar-registration, /evm-optin) →
self-paced courses (Voice of Success $497, anchored against a $10,000+ VIP program) → 1:1 / group
coaching → client-portal community. 20,000+ email list. Corporate roster referenced: KPMG, Oliver
Wyman, DHL, Emirates, Siemens Healthineers. Active — blog updated July 14, 2026 (2 days before this
walk).

**Re-audit note (2026-07-17):** the original walk's headline finding — a "404 at checkout" on the
newest-post teaser — was retracted. It turned out to be a www-only technicality: the teaser
resolves HTTP 200 on the apex host (`lisahugo.com`) in normal navigation, and only a hand-forced
`www` spelling of the URL 404s. Lisa checked from the apex side and pushed back correctly on Touch
1's reply. A full re-audit then ran across the funnel, Instagram, and LinkedIn on the apex host,
every candidate curl/grep-verified; money path and LinkedIn both came back clean. The finding below
is the one that survived that re-audit.

## Funnel Walk

- Stop 1 (Home / entry) — clean hub with a clear CTA hierarchy (free masterclass, book, About);
  narrows well, no leak.
- Stop 2 (Freebie) — two live webinar opt-ins (/iai-webinar-registration, /evm-optin), both capture
  email, evergreen countdowns, real testimonials — functioning.
- Stop 3 (Offer / sales) — $17 book sales page (/voice-of-influence) shows $47 struck to $17 with
  correct testimonials; course hub (/training, /online-trainings) is a real paid ladder (Voice of
  Success $497 vs a $10,000+ VIP program). Course buttons DO resolve to `/vos-page` and `/swnf-page`
  (both 200) — an earlier "unresolved via cta-probe" note was a false alarm.
- Stop 4 (Checkout, /voi-checkout) — the two-step order form (name/email/phone → payment) functions
  cleanly, live Stripe. The "featured story" 404 flagged in the original walk was a www-only
  artifact (see Overview) — retracted, checkout path is clean.
- Stop 5 (Audience ownership) — owns a 20,000+ email list, a 160K-download podcast, and a
  multi-page opt-in system — not dependent on rented reach.

## Evidence

- **Site vision pass:** `VISION PASS: COMPLETE — 15 of 15 required images confirmed read`
- **Pasted evidence:** none — crawl-only walk
- **Screenshots:** none promoted yet — see per-finding notes below

Re-audit (2026-07-17, apex host, curl/grep-verified): the podcast mislabel below; an IG bio-link
dead YouTube button (banked, unused); an unconfirmed dead footer `#` anchor (banked, unused,
needs DOM-position verification before use); money path and LinkedIn both confirmed clean.

## Gates

- **Gate 0:** Pass — UAE-based (Dubai; "Dubai's Leading Executive Communication Coach"); real
  reachable paid funnel ($17 book checkout + $497 courses + coaching, none login-walled); activity
  fresh (blog Jul 14 2026); audience 20,000+ email + 160K+ podcast downloads.
- **Gate 1:** Pass — solo operator; own face and voice throughout ("Message From Lisa", "1:1
  Coaching With Lisa"); Audacia Marketing Management LLC is her own company, not a gatekeeper.
- **Lane:** Lane 1 (felt leak)

## Findings — reasoning

> The **canonical, structured** copy of each finding lives in Airtable (`Findings` table): rank,
> status, depth, type, innocent explanation, evidence path. This section carries the *reasoning* —
> why it's deep vs shallow, why it stings, what was ruled out. Don't duplicate the fields here; they
> will drift.

**Rank 1 — podcast show-notes stuck on the wrong episode number**
Depth: DEEP · Type: stale/copy-paste content on the flagship trust asset
Innocent explanation: episode 68's page was duplicated as the template for 69/70/71 and the
show-notes number was never updated.
Why it matters: her podcast (160K+ downloads) is her flagship trust asset. The three most recent
episodes (`/71`, `/70`, `/69`) all render their show-notes header as "ShowNotes for Episode 68" —
only the newest three are wrong, everything from 68 back is correct. A new listener who opens the
latest episode to decide whether to subscribe sees the freshest content on the asset she's known for
looking copy-pasted, right at the moment she's deciding whether Lisa is careful about her own work.
This is the finding that replaced the retracted "404 at checkout" claim and was used as Touch 2
(turn-two, warm).
Evidence: none promoted yet — see raw archive (`docs/leads/lisa-hugo.raw.md`)

**Rank 2 — IG bio-link YouTube button 404s** *(RESERVED — unused, banked for a future touch/Loom)*
Depth: SHALLOW · Type: broken link
Innocent explanation: a typo when the button was set up.
Why it matters: on `lisa-hugo.com/link-bio` the "Lisa Hugo Marketing" YouTube button points to
`@lisahugomarketingl` (stray trailing "l"), which 404s; the correct `@lisahugomarketing` is live.
Lower stakes than Rank 1 — a secondary channel link, not the flagship asset — but a real, confirmed
dead end.
Evidence: none promoted yet — see raw archive

**Rank 3 — footer "Podcast" link (unconfirmed)** *(RESERVED — unused, needs verification)*
Depth: SHALLOW (unconfirmed) · Type: possible dead anchor
Innocent explanation: leftover markup from a nav restructure.
Why it matters: a dead `#` self-anchor exists sitewide on apex pages, but each page also carries a
working `/podcast` link, and which anchor actually sits in the footer position is unconfirmed. Do
not use without verifying DOM position first.
Evidence: none promoted yet — see raw archive

## SMYKM Hook

`her current LinkedIn series on executive presence in the Middle East — the line that how you
respond to the first cup of Arabic coffee can set the tone for the whole relationship, because in
GCC business the relationship IS the business` — **WORK** — source:
[LinkedIn post, 2026-07-16](https://www.linkedin.com/posts/lisa-hugo_executive-communication-in-the-middle-east-activity-7483431276889137152-CAlq)
(USED, Touch 1)

Fresh hook candidates (re-audit 2026-07-17, unused, for future touches — all real and cited):
- The Vinh Giang clip she sat on for months, self-conscious about how she showed up, then released
  for his "voice as an 88-key instrument" idea mirroring her own teaching —
  [IG](https://www.instagram.com/p/Daf1fLIju6O/) / [LinkedIn](https://www.linkedin.com/posts/lisa-hugo_earlier-this-year-i-had-the-opportunity-activity-7480288296053510144-94za),
  2026-07-07.
- Conditioning her two daughters that filler words were "almost as bad as a swear word," now credits
  it for their confidence as speakers — [IG](https://www.instagram.com/p/DaSH27Mlm_E/), 2026-07-02.
- Her 57th birthday post / going public about her age ("Fifty is the new thirty") —
  [IG](https://www.instagram.com/p/DaXcsv_u1Tc/), 2026-07-04.

---

*Email history lives in Airtable (`Touches` table) — every send and reply, verbatim.
Price discovery answer and anchor live on the Airtable `Leads` record.
Neither is duplicated here.*
