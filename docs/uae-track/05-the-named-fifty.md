# The Named Fifty — the attraction offer

_Decided 2026-07-28. The first paid rung of the money model. The flagship is
`02-the-offer-first-five.md`; this is what gets someone to it._

> ### The Named Fifty — AED 500, delivered in 72 hours
>
> Fifty verified, deliverable, gate-checked contacts in the UAE who match the
> clients she already has and likes. Built backwards from her own best-paying
> clients. Hers to keep, forever, whatever she does next.

---

## Why this exists

Selling a AED 2,000 + 900/call program to a stranger who has never heard of you
is a big first ask, and **0 for 9 says so.** An attraction offer's job is not to
make the profit. It is to **buy a customer.**

Five reasons this specific offer is the right one here, not a generic tripwire:

1. **It is the one thing already proven deliverable.** 373 UAE coaches found in
   14 days is not a claim, it is a log in this repo.
2. **It is a complete solution to a narrow problem**, which is the definition of
   an attraction offer. Not a sample, not a teaser.
3. **It reveals the problem the core offer solves.** She now owns a list and has
   no time, no sending domain and no idea what to write. That realisation is the
   upsell, and she reaches it herself.
4. **It cannot be consumed and walked away from the way a finding was.** This is
   the resolution to the failure that killed the funnel-fix offer: 4 of 9
   engaged leads read the finding, fixed it themselves and left. A list is an
   asset she keeps, delivered by us, and it makes us the person who has her
   list.
5. **It fixes the reply → call collapse structurally.** "Get on a call so I can
   describe a problem" went 0 for 9. "Get on a call and I hand you twenty names"
   is a different ask. That is example 8 in `examples.md`, and it costs nothing
   to test before this offer is ever built.

## What is actually delivered

| | |
|---|---|
| **Price** | AED 500, paid up front |
| **Turnaround** | 72 hours from payment, hard |
| **Deliverable** | 50 contacts: name, business, role, the link she can check, and a verified deliverable email |
| **Built from** | Her own best-paying existing clients, worked backwards into a profile |
| **Ownership** | Hers permanently, no strings, whatever she does next |

Every contact is gate-checked the same way our own leads are: UAE-based, real
business, reachable, and the email verified deliverable rather than merely
syntactically valid. **The verification is the product.** Anyone can scrape 50
names; the reason it is worth AED 500 is that all 50 land.

**Delivery cost is roughly AED 100 per list** (enrichment + verification), so
the offer funds its own delivery four times over and can run at volume while
the core offer is still unproven.

## How it is sold

**It is never cold.** The attraction offer skips the *earned right*, not the
human being. A priced offer to someone who has never replied is a cold pitch at
any price, and AED 500 does not make it not one.

Enforced: `python main.py crm-gate offer <row.json> --tier attraction` must
print PASS. That tier requires a **live thread** — a `Status` of `Reply
Received`, `Call Booked`, `Offer Sent`, `Won` (or the legacy sold/delivered
statuses), or `Asked For Price` checked. The flagship keeps the stricter
`core` tier, unchanged.

**Pick the tier by which offer you are drafting, never by which verdict you
want.** Quoting The First Five through `--tier attraction` is the one abuse this
split makes possible, and it is exactly the cold pitch the gate has always
existed to stop.

## The upsell, at the moment of delivery

She opens the list. That is the hyper-buying window and it is about ninety
minutes wide.

> "That's your fifty. Want me to send to them as well? Same list, I write every
> one by hand, and you only pay for calls that actually happen."

→ **The First Five.** AED 2,000 setup + 900 per qualified call.

Assume roughly one in four takes it. Four Named Fifty buyers plus one upsell
with two billable calls in month one nets about **AED 4,750 in 30-day cash**
against near-zero cash CAC, because acquisition is our own cold email. The model
is client-financed from the first cohort, which puts the constraint back where
it belongs: send capacity and Haytham's time.

## What this does NOT change

- **The cold opener.** Still five beats, still a call ask with two specific
  times. The Named Fifty is not pitched in a cold email, at any touch.
- **The finding.** Still RESERVED call bait, still never emailed.
- **The core offer's gate.** Unchanged, still the earned right.
- **The send ceilings, the Sunday pause, the three-touch sequence.** Untouched.

## The open risk, stated plainly

**Nobody has bought this.** It is one day old, it has never been offered to a
human, and the AED 500 price and 72-hour promise are both untested. The thing
that makes it a good bet is that the delivery is the one capability this
operation has already demonstrated at volume — not that anybody has wanted it
yet.

Test order, cheapest first: **example 8's "twenty names" call ask** costs
nothing and tests the same premise (does a deliverable in the call fix reply →
call). Only if that moves does the full AED 500 product need to exist.
