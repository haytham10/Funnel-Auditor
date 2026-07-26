# Murielle Larrière (Dubai French Tuitions)

<!-- airtable-record: TBD -->
> **Site:** https://www.dubaifrenchtuitions.com · **Profile:** none found
> **Walked:** 2026-07-13 · **Slug:** `murielle-larrière-dubai-french-tuitions`

---

## Overview

Murielle Larrière runs Dubai French Tuitions, a solo online French-tutoring business she founded in
2012 and still teaches single-handedly ("Murielle is the sole teacher"). Dubai-based, native French
teacher and DELF examiner, on Kajabi. Audience is 48,612 Instagram followers (verified business
account) plus 15,861 on Facebook. Her IG bio link points at /vsl-access, a free-masterclass VSL,
which is the real funnel entry. Published prices in AED: 2,120 (10-hour course), 2,120/m x4 (40-hour),
1,002/m x4 (Online Key Program), 233/hour (DELF prep). Real business with real students: newest
Google review is 2 days old, newest blog post is Jul 06, 2026.

## Funnel Walk

- Stop 1 (/vsl-access, the IG bio destination) — Wistia VSL loads fine on desktop and mobile; the
  ONLY call to action originally recorded on this page was "Book free call" to Calendly, with no
  email capture noted anywhere on the page. **This claim was later flagged in the raw archive as
  incorrect** (see note below) — treat the original "no email capture" reading on this stop with
  caution.
- Stop 2 (Calendly, "Book your discovery call with Murielle") — live and functional. July 2026 shows
  "No times in July"; August has real bookable slots (3, 4, 6, 10, 11, 17, 18, 20, 24, 25, 27, 31).
  Booked out for the current month, not broken. Ruled out as a finding.
- Stop 3 (/french-course-fees, the pricing page) — four price cards, all in AED, each with a "Book
  Now" button. This is the money page and it is where the funnel breaks.
- Stop 4 (the checkouts) — every "Book Now" lands on a live Stripe checkout that charges in EUR, not
  AED, and two of the four point at the wrong product entirely. Confirmed by reading the four Book
  Now hrefs in DOM order against each checkout page:
  - Card 1 "10-hour Course / 2120 AED / One time" → checkout reads "Learn French 40H - Private
    Courses (4 Instalments)", EUR 500,00 x 4 monthly payments (~EUR 2,000 total, ~8,000 AED). Wrong
    product, wrong currency, ~4x the advertised price.
  - Card 2 "40-hour Course / 2120 AED/m x 4 months" → checkout reads "Learn French 40H - Private
    Courses", EUR 2.000,00 payable in full on registration. Right product, but the advertised
    4-month payment plan becomes a single full payment at checkout.
  - Card 3 "Online Key Program / 1002 AED/m x4" → "The French Method Beginner A1: 4xpayment", EUR
    232,00 x 4. Right product, still charged in EUR.
  - Card 4 "1-hour DELF Exam Prep / 233 AED/h" → the SAME EUR 2.000,00 40-hour course checkout as
    Card 2. A buyer clicking to book a single 233 AED exam-prep hour is asked for EUR 2,000 in full.
- Stop 5 (/store, the Kajabi storefront, linked in her own site nav) — still on the unedited Kajabi
  demo template. Hero is a stock photo of a woman boxing in a gym. "Featured Courses" are the Kajabi
  sample fitness classes: "Core & Abs", "Fire Moves", "Aerobics 101", each with gym stock photography
  and placeholder copy about burning calories and building lean muscle. Every "Learn more" button
  links back to /store itself. "New Client Special Offers" is empty. This is on a French tutoring
  site.
- Also noted (secondary, same page): the FAQ at the bottom of /french-course-fees contradicts the
  price cards directly above it — FAQ says courses "start 172 AED for a 1-hour DELF preparation
  class, and full courses start at 1598 AED for 10 hours", while the live cards say 233 AED/h and
  2120 AED. Stale FAQ copy against current pricing.

## Evidence

- **Site vision pass:** `VISION PASS: COMPLETE — 9 of 9 required images confirmed read` (13
  screenshots on disk: the 9 manifest-required plus 4 extra zoomed captures taken to read the price
  cards and both Calendly months at legible scale)
- **Pasted evidence:** none — crawl-only walk. Independent confirmation of the IG bio link and
  audience via a read-only, no-login Apify profile pull: 48,612 followers, verified, business
  account, externalUrl = dubaifrenchtuitions.com/vsl-access, bio reads "FREE Masterclass".
- **Screenshots:** none promoted yet — see per-finding notes below

Machine flags rejected in the vision pass: 1 — Calendly "no availability" (the July markdown read as
a dead calendar; the August screenshot shows a dozen live bookable dates, so the flag is dead — she
is booked out, not broken).

**Note on Stop 1:** the raw archive records a later note, filed under its (dropped) Price Discovery
section, stating the Funnel Walk's original claim that /vsl-access has "no email capture anywhere on
the page" is wrong — a re-fetch found the page does have an email capture form ("Fill in the
information below") plus a second CTA the walk missed, "REGISTER FOR THE FREE CONFERENCE." The draft
that went out was built on the verified checkout finding (below), not the email-capture claim, so
this does not change the finding used in outreach — but a future session should not treat "no email
capture on /vsl-access" as confirmed. Flagging this explicitly rather than silently editing Stop 1,
since the correction itself lived in a section (`## Price Discovery`) this migration drops
unconditionally per the mapping instructions.

## Gates

- **Gate 0:** Pass — UAE base confirmed (Dubai; site, blog byline "French teacher in Dubai", Google
  Maps presence). Funnel floor confirmed (live Kajabi sales page with four priced offers and working
  Stripe checkouts). Activity floor confirmed well inside 30 days (blog post Jul 06 2026, Google
  review 2 days ago). Audience floor cleared 32x (48,612 IG, verified).
- **Gate 1:** Pass — solo operator. Founded 2012 by Murielle, "Murielle is the sole teacher", the
  Calendly is her own personal booking link, the blog is written in her name, and the checkouts bill
  her products directly. No agency, no gatekeeper.
- **Lane:** Lane 1 — a live, revenue-blocking mismatch between the advertised price and what the
  checkout actually charges.

## Findings — reasoning

> The **canonical, structured** copy of each finding lives in Airtable (`Findings` table): rank,
> status, depth, type, innocent explanation, evidence path. This section carries the *reasoning* —
> why it's deep vs shallow, why it stings, what was ruled out. Don't duplicate the fields here; they
> will drift.

**Rank 1 — Book Now buttons send buyers to the wrong checkout, in the wrong currency**
Depth: DEEP · Type: checkout/product mismatch + currency mismatch
Innocent explanation: she set the Kajabi offers up in EUR when the business served a French/European
client base, then re-priced the public pages in AED for the Dubai market without re-mapping which
offer each Book Now button points to — the kind of thing that only surfaces when someone actually
clicks through to pay, which she has no reason to do on her own site.
Why it matters: the 1-hour DELF Exam Prep card advertised at 233 AED/h and the 10-hour course card
advertised at 2,120 AED both land on Stripe checkouts for a different product billed in EUR — the
DELF card lands on a EUR 2.000,00 full-payment 40-hour private course. Every checkout on the site
charges EUR while every price on the site is quoted in AED. This is revenue-blocking, not cosmetic —
a beginner who decides to try one hour with her gets asked for the full course price instead. Used
as the Touch 1 opener (scheduled send, 09:00 Gulf).
Evidence: none promoted yet — see raw archive (`docs/leads/murielle-larrière-dubai-french-tuitions.raw.md`)

**Rank 2 — /store is still running Kajabi's unedited fitness demo template** *(RESERVED — held back for Touch 2/Loom)*
Depth: SHALLOW · Type: leftover platform demo content
Innocent explanation: /store was likely never touched after the Kajabi account was set up — the real
funnel runs through /vsl-access and /french-course-fees, so this page may simply have gone
unnoticed.
Why it matters: /store, linked from her own site nav, still shows the Kajabi demo template — gym
stock photography, "Core & Abs" / "Fire Moves" / "Aerobics 101" sample fitness classes, empty "New
Client Special Offers" — on a French tutoring site. Deliberately not spent on Touch 1, held for
Touch 2 or the Loom.
Evidence: none promoted yet — see raw archive

**Rank 3 — FAQ pricing contradicts the price cards directly above it** *(RESERVED — unused)*
Depth: SHALLOW · Type: stale copy vs. live pricing
Innocent explanation: the FAQ was written when prices were lower and never updated when the cards
were repriced.
Why it matters: the /french-course-fees FAQ says courses "start 172 AED for a 1-hour DELF preparation
class, and full courses start at 1598 AED for 10 hours," directly beneath cards reading 233 AED/h and
2,120 AED.
Evidence: none promoted yet — see raw archive

## SMYKM Hook

`the French method she teaches, the one built to get a beginner speaking in 20 minutes a day rather
than out of a grammar book` — **WORK** — source:
[her most recent post, May 12 2026](https://www.instagram.com/p/DYQAi9BNJjY/) ("Discover the French
method... speak French in just 20 minutes a day"; the POV stated plainly in an
[earlier post](https://www.instagram.com/p/DPZFb_Ok7xI/), "Stop learning French from grammar
books!"). Her hero copy also confirms the method is trademarked: "Discover The French Method™".

---

*Email history lives in Airtable (`Touches` table) — every send and reply, verbatim.
Price discovery answer and anchor live on the Airtable `Leads` record.
Neither is duplicated here.*
