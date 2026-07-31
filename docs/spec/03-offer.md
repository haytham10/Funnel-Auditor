# The money model

_Written 2026-07-31 from Haytham's Hormozi build. The offer had no home in this
repo before now — it lived in one document outside it, which is how the previous
project ended up with two competing offer files and no authority._

**Owns:** every price in this operation, the guarantee and its conditions, what
each paid engagement includes, and the order things get built in.
**Defers to:** `docs/spec/02-icp.md` — who this is sold to; `docs/spec/04-email.md`
— what an email may say, which is never a price; `copy/results.csv` — the client
results any claim is justified with; `docs/spec/01-operation.md` — the capacity
constraint every price here answers to.
**Allows:** none.

**This file is the only place a price may appear.** If code, a CSV, a skill or
another doc disagrees with a number here, that other thing is wrong. Change this
file first.

## The three shelves

The failure that rots an offer doc is not a stale number. It is a reader who
cannot tell what is being sold today from what was designed on a Tuesday. So
everything below sits on exactly one shelf, and the shelf is stated before the
detail:

| Shelf | Means |
|---|---|
| **SHIPPING** | in market now, in every email |
| **BUILT, NOT SOLD** | fully specified, never bought by anyone |
| **NOT BUILT** | designed, gated behind something that has not happened |

Nothing moves up a shelf because it is ready. It moves when its gate is true.

## The diagnosis this was built to fix

The ten free names are an attraction offer with nothing behind it — in Hormozi's
terms a **decoy**, a stripped-down free thing whose job is to make a premium look
obvious by contrast. The decoy has been shipping for months. The premium was
never built. So even a call that goes well ends with a coach saying "thanks for
the names" and nothing to say yes to.

That is a separate failure from reply-to-call being zero, and fixing it does not
fix that. But zero-for-nine means the back end has never been tested, and the
first time a call does land there needs to be something on the other side of it.

## The anchor everything is priced against

| Source | Figure |
|---|---|
| ICF 2025 Global Coaching Study | $234 average one-hour session; 12.4 active clients; $49,283 average annual coaching revenue → **≈ $4,000 revenue per client per year** |
| Kaizen (Dubai business coaching) | 1:1 programs **$2,500–$11,000/month**; mastermind tier from $500/month |
| BMC Dubai leadership programs | AED 3,500–8,000 short; AED 8,000–15,000 intermediate; AED 15,000–25,000+ executive (≈ $950–$6,800) |

**Working anchor: one closed client is worth about $3,000 to a solo UAE coach.**
Business and leadership run higher ($5,000+); life and mindset run lower
($1,000–2,000). Every price below is justified against that number, out loud, on
the call. A price nobody can justify in one sentence is a price that gets
negotiated.

---

# SHIPPING — the ten names

**Price: nothing.** This is the entire content of every cold email, and the only
offer the machine produces.

Ten real people who fit the coach's buyer profile, already pulled, handed over on
a fifteen-minute call along with why those ten and not the other forty.

**No price appears in any email**, and the mechanism holding that is described in
`docs/spec/04-email.md`. The money conversation happens on the call and nowhere
before it.

### The delivery promise has a clock on it

The close carries a time bound: *the same day*, *before the call ends*, *within a
day of us speaking*. That was added deliberately — a deliverable with no date is
an intention.

Two operational consequences, and both are real work rather than caveats:

1. **The ten must be ready on the call, or inside 24 hours of it.** Not
   researched afterwards. Whoever takes the call brings the document.
2. **The pool must be deep enough to serve concurrent calls** without repeating
   names across two coaches in the same segment.

**Breaking this promise costs more than never making it.** It is the first thing
the coach can check and it comes due before anything has been sold.

### The pivot, on the call

Load-bearing, and the order is not negotiable. The call was promised as *the ten
are yours, and why these ten and not the other forty*. **Deliver that in full
before pitching anything.**

> "That's the ten, and that's why those ten. Now — I built that list in about two
> hours. If you want, I do it at volume: I source them, write the hook, run the
> sending from my own domains so your reputation never touches it, and you get
> five of these on your calendar inside thirty days. Want me to walk you through
> what that costs?"

Then the stack, the price, the guarantee, the ask. Bonuses after the yes, or
against a specific objection.

---

# BUILT, NOT SOLD — The First Five

**Price: $1,500. Thirty days.** Nobody has bought this yet.

Haytham sources, researches, writes and sends the outbound from his own
infrastructure, and hands over **five qualified calls** with prospects who fit the
coach's ICP, booked on the coach's calendar.

The value gap, said plainly: *five calls, and a coach closing one in three makes
$3,000 on the first one. The other four are free.*

### The stack

| Component | What it is | Value |
|---|---|---|
| Sourcing | 200–300 vetted prospects, deduped against their CRM, verified addresses only | $600 |
| The hooks | One real, sourced observation per lead — the thing that makes it not spam | $900 |
| The infrastructure | 2 domains, 3 inboxes, warmed, sending in their name | $400 |
| The sending | 30 days of managed send, 25/day/inbox, replies routed to them | $800 |
| The booking | Replies worked to a booked slot on their calendar | $700 |
| **Total** | | **$3,400** |

Against **$1,500**.

### The guarantee — *The Five or I Don't Stop*

A conditional service guarantee, which is the right shape when there is no track
record to show yet.

> **Five booked calls in thirty days, or I keep sending free until you have them.
> If you have zero after thirty days, the $1,500 comes back and you keep every
> name, hook and inbox I built.**

Three conditions, stated up front, because they align incentives and screen out
bad-fit buyers rather than protecting against them:

1. They reply to interested leads within 24 hours.
2. They keep a calendar link live with real availability.
3. The ICP is locked for the thirty days. One change mid-sprint voids the clock.

**"Zero calls" is the refund trigger, not "fewer than five."** That split is
deliberate: the service half covers one through four, the refund half covers total
failure, and both halves exist so neither has to carry the whole objection alone.

### Bonuses

Revealed after the ask, or against the specific objection each one kills.

| Bonus | Kills | Value |
|---|---|---|
| **The Inbox Kit** — the 2 domains and 3 warmed inboxes, transferred at the end, theirs to keep | "What if I stop after a month?" | $400 |
| **The Reply Playbook** — the scripts for turning a reply into a booked call, and what to say in the first five minutes of one | "I won't know what to do when someone answers" | $300 |
| **The Do-Not-Touch List** — their CRM and contacts deduped out before a single send | "Don't email people I already know" | $200 |

$900 of bonuses on a $3,400 stack, against $1,500.

### Scarcity and urgency, both honest because both are true

- **Cap: six active clients. Two new starts per month.** State the real current
  number on the call. Actual capacity is four to eight; six is the number to say
  and hold.
- **Urgency is the start date, not the price.** Sprints kick off on the 1st and
  the 15th. Miss one, wait two weeks. **Never discount to create urgency** — a
  discount that manufactures a deadline teaches the buyer the price was soft.

### The name

**The First Five.** Goal, interval, and a number specific enough to be checkable.
Alternates worth testing: *The Thirty-Day Five*, *Five Booked*.

---

# NOT BUILT — everything after the first sale

Each of these is designed and none of them exists. The gate on each is a fact
that must be true, not a date.

## The Ninety — the upsell

**Gate: The First Five has been delivered at least once, in full.**

Offered on the same call, immediately after the yes. The problem The First Five
creates is that five calls is a sample, not a pipeline, and it runs out in thirty
days.

> "Five calls tells you whether this works. It doesn't fill your year. If you want
> the ninety-day version, the $1,500 you just paid rolls into month one — so it's
> $1,000 today instead of $1,500, then $2,500 a month for two more."

**$2,500/month × 3 months, with the $1,500 pilot rolling in as credit.** Total
90-day collection **$6,500**, against a target of 15–20 booked calls.

Rollover is the right upsell shape here: it makes the pilot feel like a down
payment rather than a sunk cost, and it discounts nothing.

**BAMFAM** — before the call ends, book the week-one check-in. Never leave a sold
client without the next meeting on the calendar.

## The downsells — for the no

**Gate: The First Five has been sold three times at full price.** Introducing
these earlier means selling the cheap thing to everyone and never testing the
premium, which is the most expensive mistake available here.

In order. **Never drop the price on the same thing** — change how they pay, or
change what they get.

**1 · Payment plan.** Same product, different cadence. $750 now, $750 the day
call number three is booked, card on file. Holds the price at $1,500 and moves
the second half behind proof.

**2 · The List — $497.** A feature downsell, and a different product. Fifty
vetted prospects in their niche, each with a real sourced hook and a verified
email, in seven days. They send it themselves. This is the cheapest thing here to
deliver — it is the existing pipeline's output with no sending attached — and it
is the right catch for a coach who wants to try before handing over their
outbound.

> "Then let's not do the sending. I'll hand you fifty of them, hook written, email
> verified, and you send it from your own inbox. Four ninety-seven, seven days."

**3 · The Build — $997.** One-time, no ongoing hours. Domains, inboxes, list,
copy and sequence loaded into their own Smartlead or Instantly, handed over
running. For the coach who wants to own it. Zero ongoing capacity cost, which
makes it the best downsell to take when all six slots are full.

The seesaw: no to $1,500 → payment plan → no → The List → still curious about
volume → The Build.

## The Desk — continuity

**Gate: one pilot has actually produced five booked calls, and the client
offered it has been through that pilot.**

**$2,000/month**, month to month. Ongoing sourcing and sending, standing
pipeline.

Entry mechanic is a **waived fee**, the cleanest of the options:

> "The $1,500 setup is waived if you start on the monthly. You've already paid it
> once and it doesn't need paying twice."

Churn safeguards, in the order they matter:

1. **Prepaid quarter at $5,400** (10% off $6,000). Collects three months up front
   and removes three renewal decisions.
2. **Bill on the day of their best call**, not the 1st. The invoice lands next to
   the reason for it.
3. **Earned lifetime rate.** At six months the $2,000 locks for life. Leaving then
   costs the rate, not just the service.
4. **Exit interview on every cancel, with no save attempt.** The reason is worth
   more than the recovered month.

Ceiling at capacity: six slots × $2,000 = **$12,000/month recurring**, plus List
and Build sales that cost no capacity at all.

---

# The assembled sequence

```
cold email          ->  ten free names           SHIPPING
15-minute call      ->  hand over the ten, then The First Five      $1,500
same call, on yes   ->  The Ninety               rollover, $6,500 / 90 days
same call, on no    ->  payment plan -> The List ($497) -> The Build ($997)
after the pilot     ->  The Desk                 continuity, $2,000/mo
```

# 30-day cash math

Per client, The First Five:

| | |
|---|---|
| Cash cost to acquire (cold email: data, domains, verification, amortised) | ~$50 |
| Fulfilment, 30 days (inboxes, Smartlead share, Apify credits, verification) | ~$120 |
| **Cost to get and fulfil** | **~$170** |
| **30-day cash collected** | **$1,500** |
| **Ratio** | **≈ 8.8×** |

The client-financed-acquisition bar is cleared by a wide margin, and **that is
the tell, not the win.** Clearing it that easily means cash was never the binding
constraint here — hours are. The correct response is not more volume at a lower
price. It is holding the six-slot cap and raising the price once the guarantee has
been paid out on and survived.

At capacity with the upsell taken: 6 × $2,500/mo = $15,000/month against roughly
$720 of fulfilment.

# Build order

Do not deploy this at once. Each step is gated on the one before it being true.

1. **Sell The First Five three times at $1,500.** Nothing else exists. No
   retainer language on the call, no continuity. Three sold pilots is the dataset.
2. **Deliver five calls, once.** Until one pilot has produced five booked calls,
   the guarantee is a liability and The Ninety has nothing behind it. **This is
   the single gate** — everything below it waits here.
3. **Add the downsells.** The List and The Build are deliverable today. They stay
   off the table until The First Five has a track record.
4. **Add The Ninety**, once delivery is reliable rather than once it is possible.
5. **Add The Desk last**, and only to a client who has already been through a
   pilot.
6. **Raise the price** when the extra cash from yeses stops offsetting the nos.
   $1,500 is a launch price, not a final one.

# What is unknown

- **Nothing on this page has been sold.** Every price is reasoned from the value
  anchor and none is validated by a transaction.
- **The guarantee has never been tested.** Its cost is unknown until it is paid
  out on once, and step 6 above deliberately waits for that.
- **The pool depth needed for same-day delivery is unmeasured.** The promise
  assumes ten fresh names per call, per segment, on demand.
