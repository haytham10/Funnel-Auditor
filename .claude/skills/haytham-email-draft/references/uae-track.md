# UAE Track — the offer register, the turn-two, and the money email

Read this whenever the lead lives in the UAE Lead CRM
(`collection://5efbdd9b-1e19-468c-96db-f94a525846e0`). Everything in
voice.md, gate.md, mechanics.md, and critical-failures.md still applies in
full — this file adds the UAE-specific layer on top: how prices are
quoted, what the turn-two sells, the guarantees, and the downsell ladder.

> **Changed 2026-07-24.** This file used to be built around the price
> discovery email, and price discovery used to be a hard gate before any
> priced offer. That premise has been falsified (100 touched leads, the
> question asked 3 times, 3 answers, all `Refused to name`, 0 numbers).
> Nobody names a budget to a stranger over email. The question moved to
> the call; the gate moved to "have you earned the right to name a
> number"; and the turn-two stopped offering a free Loom and started
> offering a paid fix. See docs/journal.md, 2026-07-24.

---

## AED framing (how the price is said)

- **Track A is 735 AED. Track B is 2,575 AED.** These are the $200 / $700
  prices, quoted natively (pegged conversion, rounded up to the nearest 5
  so the AED figure is never below the dollar price). Not a discount, not
  a regional price, not a different number. The price never moves.
- **Quote AED only.** Never the dollar figure, never both currencies in
  one breath. "735 AED flat" reads local; "$200 (about 735 AED)" reads
  like a foreign freelancer converting currencies at her. If SHE talks in
  dollars, mirror her currency in that reply and stay consistent from
  then on — the point is her comfort, not a rule about dirhams.
- **Never present the AED figure as a favor or a localization.** It's the
  same price. Saying "for UAE clients I do 735 AED" implies a special
  rate that invites negotiation.
- All the money-email field rules from mechanics.md apply unchanged:
  guarantees stated boldly and unprompted, one CTA (price + one concrete
  next step), bonuses answer stalls, the number never drops.

---

## THE 48-HOUR LEAK FIX — 500 AED, paid after (the turn-two offer)

The rung the ladder was missing. It converts a stranger into a customer,
which is the only thing that has never happened on this track.

- **500 AED, paid after.** Access on their side, the specific banked
  finding fixed and live within 48 hours, they pay only once it's live and
  working.
- **Alternative: 365 AED paid up front**, which also includes the full
  12-point teardown of the rest of the funnel. Offer this only if they
  hesitate on the shape, never as the opening number.
- **It is NOT gated by `crm-gate offer`.** The Leak Fix is the thing that
  EARNS the right to name the Sprint number, so gating it would deadlock
  the motion. Only the priced Sprint / Track A / Track B money email needs
  a gate PASS.
- Why this replaced the Loom: a Loom is high-effort for the prospect
  (watch a video, then decide) and low dream-outcome (you describing a
  problem they now feel worse about). It was offered to Ben Pringle, Lisa
  Hugo and Lucia Csobonyei and taken by none of them. The paid fix is the
  same finding, but the offer is their problem going away, at zero risk,
  for the price of a dinner.

**The turn-two script** (adjust to the thread, never paste — the bespoke
check applies):

> Rather than talk about it, want me to just fix it? Access on your side,
> live in 48 hours, and you only pay if it's working. 500 AED. If it's
> easier, here's my calendar and I'll walk you through what I'd do first:
> [link]

**Every turn-two ends in a single-tap next step or a paid tiny yes.**
Never a discovery question, never a menu, never a soft exit. Those two
endings are the only legal ones.

Logging: a sold Leak Fix moves the row to `Leak Fix Sold`, then
`Leak Fix Delivered` once it's live, with the amount in `Cash Collected`
and `Est. Value` = `Leak Fix (500 AED)`.

---

## THE SPRINT — the priced offer, as a stack

**"The Booked-Out Funnel — 5-Day Sprint for UAE Coaches" · 2,575 AED.**
(Name alternates to test: "The 5-Day Leak-to-Launch", "The Dubai Coach
Funnel Sprint".) Never quote it as "I'll fix your funnel for 2,575 AED" —
that is directly price-comparable to a Fiverr gig. A stack whose summed
value dwarfs the price is comparable to nothing.

| Component | Value |
| --- | --- |
| The Leak Map — written 12-point audit of every leak, fixed or not | 900 AED |
| Rebuilt opt-in + sales page (copy, design, build) | 4,500 AED |
| Checkout / booking flow fixed + tested end-to-end from a clean device | 1,200 AED |
| 5-email welcome sequence written and installed | 2,000 AED |
| Mobile + speed pass | 800 AED |
| Loom handover walkthrough | 600 AED |
| **Stacked value** | **10,000 AED** |

**Bonuses, each killing one objection:**
- **The Leak Map** (900 AED) — "what if you miss something"
- **The Send-Ready Launch Kit** (1,500 AED) — 5 emails + 10 captions to
  point traffic at the new funnel; kills "then what, it just sits there"
- **The 30-Day Tune-Up** (1,200 AED) — one revision round after real data;
  kills "what if it doesn't work first time"

**Scarcity, both honest and true** (never invent either):
- Growth-rate cap: "I take 2 new builds a week. Solo, no team, that's the
  real ceiling."
- Rolling slot urgency: "next open build slot is [date]."

⚠️ **The price holds at 2,575 AED.** Do NOT quote 3,600. Zero closes have
landed; raising the price and restructuring the offer at once means you
won't know which one moved. 3,600 is the documented next step, gated on 2
closes (docs/uae-track/02-the-offer-gso-v2.md).

---

## THE GUARANTEES — both, named, stacked, unprompted

Risk is the #1 objection, and the market brief's own conclusion is that
the blocker is trust. Both guarantees go in every money email, stated
boldly before any objection arrives, by name:

1. **The Live-or-Free Guarantee.**
   > Your funnel is live, tested end-to-end from a clean device, and
   > taking bookings within 5 working days of getting access. If it isn't,
   > you don't pay, and you keep everything I've built.

2. **The First Booking Guarantee.**
   > If you don't take one booking through the new funnel within 30 days
   > of launch, I keep working, copy, offer, sequence, free, until you do.
   > Condition: you send traffic to it.

**The condition on ② is load-bearing** and is never dropped to sound
generous. It aligns incentives and screens out buyers who won't do the
work; without it the guarantee is unbounded and reads as desperate.

---

## THE DOWNSELL LADDER — never drop the price for the same thing

The standing rule is "the price never drops, the scope does". Without a
named ladder that resolves in the moment, which is exactly when people
cave. Work the rungs in order:

1. **Payment Plan Downsell** — 1,300 AED to start, 1,275 AED on launch
   day. Same total, same scope. ("It costs too much" almost always means
   "it costs too much up front.")
2. **Feature Downsell, "The Minimum"** — one flagship page done right
   (copy, design, build, mobile), 1,800 AED. Named deliberately: "The
   Minimum" implies they should get at least that.
3. **The 1-10 check, after two downsells** — "how badly do you want this
   fixed, 1 to 10?" 8+ → put them on the payment plan. 7 or below →
   recombine to whatever their 10 actually is, or let it go.

Never invent a rung, never invent a discount, never skip to rung 3.

## The lifecycle this track logs against

```
Sourced → Qualifying → Audit Ready → Draft Ready → (Scheduled)
  → Outreach Sent → Reply Received
  → [Leak Fix Sold → Leak Fix Delivered  OR  Call Booked]
  → Offer Sent → Won
```

Off-ramps: Lost, Dormant, Disqualified. There is no "Loom Sent" status in
this CRM, and no Loom offer either — the turn-two artifact is the paid
Leak Fix, offered inside Reply Received and logged in the page body's
Email Thread Log with an `Artifact:` line. Status changes on sends (only
after Haytham confirms a send, as always):

- First send: Audit Ready → Outreach Sent (Touch # = 1, Sequence = Cold).
  The opener carries the #1 finding from the row's `Findings Bank`.
- Cold follow-ups (Touch 2-3, no reply): stays Outreach Sent. Cadence:
  Touch 2 day 3, Touch 3 day 9. After Touch 3 with no reply → Dormant,
  Next Action set 2-3 weeks out. **There is no Touch 4 on this track.**
  Each follow-up must carry something new — see "What each cold touch
  carries" below.
- She replies: → Reply Received, Sequence = Warm.
- The turn-two offers the paid Leak Fix or a call. She buys it: →
  `Leak Fix Sold`, then `Leak Fix Delivered` once it's live (log
  `Cash Collected`). She books instead: → `Call Booked`.
- She asks what it costs, at any point: check `Asked For Price`. That is
  the highest-intent signal in the CRM and it earns the money email on its
  own.
- The priced Sprint offer goes out: → Offer Sent. **`python main.py
  crm-gate offer` must print PASS before that offer email is even
  drafted** — it now checks that she has EARNED a number (an earned status,
  or `Asked For Price`), not that she named one.
- Paid: → Won. Explicit no or warm-thread ghost after 8-10 touches: →
  Lost with Lost Reason.

---

## What each cold touch carries (the follow-up payload rule)

A cold follow-up that just bumps is a wasted send and a spam signal — it
eats that inbox's day budget and gives the reader nothing. Every touch on
this track carries a payload, and the send gate enforces it
(`python main.py crm-gate send <row.json> --sends-today N --touch T
--carries X --inbox "<the lead's Inbox>"` must print PASS before a
follow-up enters the queue — `--inbox` is the lead's assigned `Inbox`
label, and `--sends-today` is THAT inbox's own count, since each inbox has
its own ceiling):

- **Touch 1:** `Findings Bank` #1 — the lowest-ranked `UNUSED` entry,
  **never** whatever the page body's "strongest verified finding" prose
  names, if the two disagree. They can disagree: a walk's narrative may
  describe the most compelling finding even when the bank correctly tagged
  that exact one `RESERVED | DEEP` (the call bait). Read the bank property
  itself, and pass `--opener-rank <N>` on the touch 1 `crm-gate send` call
  so the gate can confirm the rank you built from isn't `RESERVED` and is
  actually the lowest `UNUSED` rank. (Added 2026-07-24 — a draft was once
  built from the narrative instead of the bank and emailed the exact
  finding the bank was reserving for the call.)
- **Touch 2 (day 3) and Touch 3 (day 9):** exactly one of
  - `second-finding` — the next UNUSED `Findings Bank` entry (the gate
    checks it exists and never draws the `RESERVED` deep finding, which is
    held for the call; never invent one at draft time). Named as a felt
    cost with its innocent explanation, fix left vague — naming a second
    cost is not the Adrienne mistake, teaching a second fix is. If the
    second finding is deep, name that it exists and costs her, never the
    fix (the deep-finding fix is call-only — see mechanics.md free-value cap).
  - `leak-fix-offer` — one line offering the paid 48-Hour Leak Fix (500
    AED, paid after) or the calendar. On a COLD thread it stays a one-line
    offer, no link. (`loom-offer` is still accepted by the gate as a
    deprecated alias, so in-flight rows don't break, but nothing new
    should declare it.)
  - `disambiguating-question` — direct binary, no soft exit ("Should I
    stop following up, or is this still on your radar?"). The natural
    Touch 3 closer.

The draft must actually carry what the gate was told (gate.md checks
this). After Haytham confirms the send, the logging step flips the used
bank entry to `USED-TN` in the `Findings Bank` property.

---

## PRICE DISCOVERY (retired as an email step — falsified 2026-07-24)

**Do not draft a price discovery email.** The question no longer goes out
over email at all. It is asked on the call, if at all.

**What was tested:** one short reply, sent while the thread was warm,
asking what she'd pay before any number of ours was on the table. The
whole track was built on it.

**What it produced:** across 100 touched leads, 182 touches and 9 replies,
the question was asked 3 times. It produced 3 answers, all
`Refused to name`, and 0 numbers. Two of the three refusers responded by
asking *us* for a price instead. Nobody names a budget to a stranger over
email, and the refusal turned out to be a TRUST signal, not a price
signal.

**What replaced it:**
- At turn-two, the paid 48-Hour Leak Fix or the calendar — a paid tiny yes
  or a single tap, never a question.
- If she asks "how much?", **answer with the number.** Do not flip the
  question back at her. That flip is what produced two of the three
  refusals. Check `Asked For Price` on her row, then quote the Sprint with
  both guarantees.
- The budget conversation, if it is ever worth having, happens on the
  call.

The `Price Discovery Answer` and `Discovery Anchor` fields stay in the CRM
and stay populated when a lead volunteers anything — the verbatim answers
are still the best qualitative data in the system. They are **advisory**
now: `crm-gate offer` reports them, it no longer blocks on them.

**Logging (advisory, but still verbatim when it happens):**
- `Price Discovery Answer`: her answer VERBATIM. Her exact words, her
  currency, her hedges. Never summarized, never cleaned up.
- `Discovery Anchor`: compare her number to the track price she'd be
  offered (735 AED Track A, 2,575 AED Track B; convert her figure at
  ~3.67 AED/USD if she answered in dollars, then compare):
  - clearly above → `Above 735 AED` / `Above 2575 AED`
  - within ~10% → `At 735 AED` / `At 2575 AED`
  - clearly below → `Below 735 AED` / `Below 2575 AED`
  - no number (dodged, or gave only an obstacle) → `Refused to name` —
    the verbatim answer still carries the data.
- `Price Discovery Sent` is a legacy status. Do not move new leads into
  it. Existing rows sitting there are worked like `Reply Received`.
- Page body, Price Discovery section: whatever she volunteered, verbatim,
  with the anchor.

**What her answer changes — and what it never changes:**
- It never changes the price. A low anchor is market data, not
  permission to discount. This is hard rule territory.
- It may change WHICH offer gets made (a real-volume operator anchoring
  high might be a Sprint conversation rather than a Leak Fix one).
- A below-anchor answer changes the offer email's emphasis, not its
  number: lead harder with both named guarantees.
- `Refused to name` is a TRUST reading, not a price reading. She withheld
  a number because she doesn't yet believe the outcome. The answer is more
  risk reversal, never a smaller number.
- An obstacle answer feeds the offer email directly: the matching bonus
  or downsell rung goes in up front.

**The gate:** before drafting the priced Sprint offer, dump the lead's
fresh row to JSON and run `python main.py crm-gate offer <row.json>`. It
now checks that the lead has EARNED a number — an earned `Status`
(`Call Booked`, `Leak Fix Sold`, `Leak Fix Delivered`, `Offer Sent`,
`Won`) or `Asked For Price` checked. Quote its literal PASS line when
reporting the draft. No PASS, no money email — take it up with the CRM,
not the gate. The 500 AED Leak Fix at turn-two is NOT gated.

---

## Silence handling in this track

Same as mechanics.md, with the corrected lines (the old "no pressure
either way" phrasing is banned like every other weak closer):

- "Are you already handling this, or would it be easier if I took it off
  your plate?"
- "Should I stop following up, or is this still on your radar?"

Direct binary questions. There is always still a concrete thing to say
yes to.

## The daily ceiling — one per inbox

There are two sending inboxes (Inbox 1 = auto-mate.one, Inbox 2 =
gethaytham.com), each its own domain with its own ceiling. A lead's `Inbox`
property says which one its whole thread rides. The ceiling is TOTAL sends
leaving THAT inbox today — openers, follow-ups, warm replies, both tracks.
Each inbox has its own ramp in `send_cap.json`, 20 → 25 → 30 by Haytham's
explicit call only (`python main.py send-cap status --all` shows every
inbox's cap and ramp reminder; missing/invalid state fails closed to 20 per
inbox; 30 is the hard cap for ONE inbox — more volume means more inboxes).
That inbox's follow-ups eat its budget first, its new openers get what's
left — enforced at queue time by `python main.py crm-gate send <row.json>
--sends-today N --touch T --inbox "<the lead's Inbox>" [--followups-due M |
--carries X]` (`--sends-today` = that inbox's own count).

**Which inbox, and how the draft is created:** the draft must land in the
lead's assigned inbox. Inbox 1 uses the Gmail MCP `create_draft` (the
PreToolUse hook lints it). Inbox 2 uses `python main.py
gmail-gethaytham draft <to> <subject> <body> [--thread-id T --in-reply-to
M]` — the SAME copy rules apply and are enforced in code on this path too
(`audit/draft_lint.py`, shared with the hook: bare domains/emails and
em-dashes block the draft, subject and body both). A new lead with a blank `Inbox` is
routed and assigned by uae-tick at queue time (`python main.py inbox
route`); don't invent an inbox here — draft into the one the row already
carries.

This skill drafts; the uae-tick skill owns the per-inbox daily count. If a
draft request would obviously blow past an inbox's ceiling (a batch of 30
"for today"), say so and draft for the queue, not for the day.
