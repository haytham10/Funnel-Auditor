# UAE Track — the offer register, the turn-two, and the money email

Read this whenever the lead lives in the UAE Lead CRM
(`collection://5efbdd9b-1e19-468c-96db-f94a525846e0`). Everything in
voice.md, gate.md, mechanics.md, and critical-failures.md still applies in
full — this file adds the UAE-specific layer on top: how prices are
quoted, what the turn-two sells, the guarantees, and the downsell ladder.

> **Changed 2026-07-27 — the offer is now The First Five. We sell booked
> calls.** Retired and not to be reinstated: Track A (735 AED), Track B /
> "The Booked-Out Funnel" (2,575 AED), the 500 AED 48-Hour Leak Fix, the
> free Loom, the 3,600 AED next step, and the Live-or-Free / First Booking
> guarantees. Full spec: `docs/uae-track/02-the-offer-first-five.md`.
>
> Why: 589 leads, 0 AED. Findings don't sell — 4 of 9 engaged leads fixed
> the finding themselves and left, and a third of findings failed under
> scrutiny. Nothing ever died on price. The mechanical cause of 0 calls
> from 9 replies is that a question-shaped CTA cannot produce a booking.
>
> **Every close is now a call ask with two specific times.**
>
> (Changed 2026-07-24, still true: price discovery as an email step was
> falsified — 100 touched leads, the question asked 3 times, 3 answers, all
> `Refused to name`, 0 numbers. Nobody names a budget to a stranger over
> email. The question moved to the call.)

---

## AED framing (how the price is said)

- **The First Five is 1,500 AED setup, credited against the first three
  calls, then 600 AED per call that actually happens.** Native AED, not a
  conversion of anything. The price never moves.
- **Quote AED only.** Never a dollar figure, never both currencies in one
  breath. "1,500 to set up" reads local; "$400 (about 1,500 AED)" reads
  like a foreign freelancer converting currencies at her. If SHE talks in
  dollars, mirror her currency in that reply and stay consistent from
  then on — the point is her comfort, not a rule about dirhams.
- **Never present the AED figure as a favor or a localization.** It's the
  price. Saying "for UAE clients I do 1,500" implies a special rate that
  invites negotiation.
- All the money-email field rules from mechanics.md apply unchanged:
  guarantees stated boldly and unprompted, one CTA (price + one concrete
  next step), bonuses answer stalls, the number never drops.

---

## THE TURN-TWO — the call ask (what happens the moment they reply)

The moment a cold lead replies, the next message asks for a call with two
specific times. Not a fix, not a Loom, not a question about their business.

**Why this is the whole ballgame:** reply-to-call on this track is 0 of 9. The
finding earns the reply at 7.4% against a 1-5% benchmark — that part works. What
never worked is what came next, because nothing ever asked for the call.

- **Two named times, one word to accept.** "I can call Tuesday around 4, or
  Wednesday morning, whichever is less annoying." Not "do you have time this
  week" (that is the vague ask that stalled Louise and Helen), not a calendar
  link as the opening move, and never both — a price-or-calendar pair is a menu
  by this track's own definition, and the no-menu rule is written four times.
- **Never a new finding.** The turn-two converts the finding already given into
  an ask. Lisa, Ben and Wafa all received a second finding at turn-two and all
  three threads died.
- **Never a question in answer to a buying question.** If she asks what it
  costs, the number goes in the reply. Flipping the question back is what
  produced two of the three `Refused to name` answers.
- **One credibility sentence and one true scarcity line.** "I run four of these
  at a time" is arithmetic, not tactics — each client needs its own sending
  domain and its own slice of the daily ceiling.
- **The friction sentence:** "All I need from you is about twenty minutes at
  the start. After that you do not hear from me until there are calls on your
  calendar."

**A booked call moves the row to `Call Booked`** — which is also the status that
passes `crm-gate offer`. The call is the rung that earns the number, so the
priced offer is quoted after it, never before.

> **Retired 2026-07-27, do not reinstate:** the 500 AED 48-Hour Leak Fix and its
> 365 AED up-front variant, the free Loom (offered three times, taken zero), and
> the price-or-calendar turn-two script. The Leak Fix existed to convert a
> stranger into a customer so that a bigger number could be quoted later; The
> First Five sells the call itself, so the extra rung is gone.

---

## THE FIRST FIVE — the priced offer, as a stack

**"The First Five — 30 Days to a Booked Calendar, for UAE Coaches."**
(Alternates to test: "Five Calls, Thirty Days", "The Booked Week".)

**AED 1,500 setup, credited back against the first three calls. Then AED 600
per qualified call that actually happens.** No retainer, no contract, no minimum
term. Billing starts at call four.

Never quote it as a flat fee for a service — that is directly price-comparable
to an agency retainer. A stack whose summed value dwarfs the price is comparable
to nothing.

| Component | Value |
| --- | --- |
| The Client Mirror — ICP built backwards from their own best-paying clients | 1,800 AED |
| The Named List — verified, deliverable, gate-checked contacts | 2,400 AED |
| The Clean Domain Shield — separate sending domain, warmed, SPF/DKIM/DMARC | 3,000 AED |
| The Written Opener — every message built on something real about that person | 3,600 AED |
| The Price-First Filter — prospects told what they charge before a call is booked | 1,200 AED |
| The Show-Up System — confirmation and reminder sequence | 1,200 AED |
| The Weekly Read — what went out, what replied, what booked, what's changing | 900 AED |
| **Stacked value** | **14,100 AED** |

**The comparison she makes for herself:** appointment-setting agencies charge
7,300-22,000 AED/month whether they deliver or not. A coach closing one in four
5,000 AED programs makes 1,250 AED per call taken, and pays 600.

**Scarcity, honest and true** (never invent it): "I run four of these at a
time. Solo, no team, that's the real ceiling." Plus rolling slot urgency: the
next onboarding date, real and honoured. **Exactly one scarcity line per money
email.** GSO v2 registered honest scarcity in two places and shipped it zero
times across every sent email in the repo — the lines existed and were never
said. Do not let that repeat.

⚠️ **The price holds until two clients are delivered.** Raise in stages, never
discount, add value instead.

> **Retired 2026-07-27:** Track A (735 AED), Track B / "The Booked-Out Funnel"
> (2,575 AED) and its 10,000 AED component stack, the 3,600 AED next step, and
> every bonus attached to them. Do not quote any of those numbers.

---
## THE GUARANTEES — both, named, stacked, unprompted

Risk is the #1 objection, and the market brief's own conclusion is that
the blocker is trust. Both guarantees go in every money email, stated
boldly before any objection arrives, by name:

1. **The No-Show, No-Charge Guarantee.**
   > You are billed only for calls where a real, qualified person actually
   > shows up. Cancellations, no-shows and time-wasters are on me, not you.

2. **Five or Free.**
   > I'll put five qualified calls on your calendar in your first 30 days.
   > If I don't, the setup fee comes back and you keep everything I built,
   > the domain, the warmed inboxes, the list, the copy, all of it.

**The condition on ② is load-bearing** and is never dropped to sound
generous. It bounds the promise to a window and a number; without it the
guarantee is unbounded and reads as desperate. A performance structure is
deliberate here: with zero case studies, perceived likelihood is the
binding constraint, and paying-only-for-outcomes makes it nearly
irrelevant.

> **Retired 2026-07-27:** the Live-or-Free Guarantee ("your funnel is live
> and taking bookings within 5 working days") and the First Booking
> Guarantee. Both promised funnel delivery, which The First Five does not
> do. The discipline is unchanged — both named, stacked, stated unprompted,
> condition intact, never softened to sound generous.

---

## THE DOWNSELL LADDER — never drop the price for the same thing

The standing rule is "the price never drops, the scope does". Without a
named ladder that resolves in the moment, which is exactly when people
cave. Work the rungs in order:

1. **Fewer calls, same rate** — the setup fee stands, the guarantee window
   scales to three calls instead of five. Same per-call price, smaller
   promise. ("It costs too much" almost always means "it costs too much
   before I see anything.")
2. **Setup deferred** — no setup fee, 750 AED per call for the first five,
   reverting to 600 after. They pay only for outcomes and the premium
   covers the risk. Delays cash, so never the opening move.
3. **The 1-10 check, after two downsells** — "how badly do you want the
   calendar full, 1 to 10?" 8+ → rung 1. 7 or below → recombine to
   whatever their 10 actually is, or let it go.

Never invent a rung, never invent a discount, never skip to rung 3.

## The lifecycle this track logs against

```
Sourced → Qualifying → Audit Ready → Draft Ready → (Scheduled)
  → Outreach Sent → Reply Received
  → Call Booked
  → Offer Sent → Won
```

Off-ramps: Lost, Dormant, Disqualified. `Leak Fix Sold` and
`Leak Fix Delivered` still exist as LEGACY statuses so historical rows keep
gating, but nothing new reaches them — the turn-two artifact is a call ask,
so a warm thread now goes Reply Received → Call Booked → Offer Sent. There
is no "Loom Sent" status and no Loom offer. Status changes on sends (only
after Haytham confirms a send, as always):

- First send: Audit Ready → Outreach Sent (Touch # = 1, Sequence = Cold).
  The opener carries the #1 finding from the row's `Findings Bank`.
- Cold follow-ups (Touch 2-3, no reply): stays Outreach Sent. Cadence:
  Touch 2 day 3, Touch 3 day 9. After Touch 3 with no reply → Dormant,
  Next Action set 2-3 weeks out. **There is no Touch 4 on this track.**
  Each follow-up must carry something new — see "What each cold touch
  carries" below.
- She replies: → Reply Received, Sequence = Warm.
- The turn-two asks for a call with two specific times. She accepts: →
  `Call Booked`. That is the rung that earns the number, and it is also
  what passes `crm-gate offer`.
- She asks what it costs, at any point: check `Asked For Price`. That is
  the highest-intent signal in the CRM and it earns the money email on its
  own.
- The priced First Five offer goes out: → Offer Sent. **`python main.py
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
  - `call-ask` — one line proposing a call at two specific times. On a
    COLD thread it stays a one-line ask, no link, no calendar URL.
    (`leak-fix-offer` and `loom-offer` are still accepted by the gate as
    deprecated aliases, so in-flight rows don't break, but nothing new
    should declare either.)
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
- At turn-two, a call ask with two specific times — a one-word yes, never
  a question about her business.
- If she asks "how much?", **answer with the number.** Do not flip the
  question back at her. That flip is what produced two of the three
  refusals. Check `Asked For Price` on her row, then quote The First Five
  with both guarantees by name.
- The budget conversation, if it is ever worth having, happens on the
  call.

The `Price Discovery Answer` and `Discovery Anchor` fields stay in the CRM
and stay populated when a lead volunteers anything — the verbatim answers
are still the best qualitative data in the system. They are **advisory**
now: `crm-gate offer` reports them, it no longer blocks on them.

**Logging (advisory, but still verbatim when it happens):**
- `Price Discovery Answer`: her answer VERBATIM. Her exact words, her
  currency, her hedges. Never summarized, never cleaned up.
- `Discovery Anchor`: a LEGACY select whose options are still worded
  against the retired Track A / Track B prices (`Above/At/Below 735 AED`,
  `Above/At/Below 2575 AED`). Do not add new options and do not read the
  labels as live pricing — they are historical buckets kept so the existing
  study data still groups. For a fresh answer the only option that carries
  meaning is `Refused to name`; everything else is better captured in the
  verbatim `Price Discovery Answer`.
- `Price Discovery Sent` is a legacy status. Do not move new leads into
  it. Existing rows sitting there are worked like `Reply Received`.
- Page body, Price Discovery section: whatever she volunteered, verbatim,
  with the anchor.

**What her answer changes — and what it never changes:**
- It never changes the price. A low anchor is market data, not
  permission to discount. This is hard rule territory.
- It may change the EMPHASIS (a coach anchoring high is a
  full-First-Five conversation; one anchoring low starts at a downsell
  rung), never the number.
- A below-anchor answer changes the offer email's emphasis, not its
  number: lead harder with both named guarantees.
- `Refused to name` is a TRUST reading, not a price reading. She withheld
  a number because she doesn't yet believe the outcome. The answer is more
  risk reversal, never a smaller number.
- An obstacle answer feeds the offer email directly: the matching bonus
  or downsell rung goes in up front.

**The gate:** before drafting the priced First Five offer, dump the lead's
fresh row to JSON and run `python main.py crm-gate offer <row.json>`. It
checks that the lead has EARNED a number — an earned `Status` (`Call
Booked`, `Offer Sent`, `Won`, or the legacy `Leak Fix Sold` / `Leak Fix
Delivered`) or `Asked For Price` checked. Quote its literal PASS line when
reporting the draft. No PASS, no money email — take it up with the CRM, not
the gate. **The turn-two call ask is NOT gated**: it is the thing that
earns the number, so gating it would deadlock the motion it exists to
start.

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
