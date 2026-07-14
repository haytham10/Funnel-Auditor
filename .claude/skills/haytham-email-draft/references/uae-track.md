# UAE Track — pricing register + the price discovery email

Read this whenever the lead lives in the UAE Lead CRM
(`collection://5efbdd9b-1e19-468c-96db-f94a525846e0`). Everything in
voice.md, gate.md, mechanics.md, and critical-failures.md still applies in
full — this file adds the UAE-specific layer on top: how prices are
quoted, and the one email type that exists only in this track.

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
  guarantee stated boldly and unprompted, one CTA (price + one concrete
  next step), bonuses answer stalls, the number never drops.

## The lifecycle this track logs against

```
Sourced → Qualifying → Audit Ready → Outreach Sent → Reply Received
  → Price Discovery Sent → Offer Sent → Call Booked → Won
```

Off-ramps: Lost, Dormant, Disqualified. There is no "Loom Sent" status in
this CRM — the artifact (turn-two walkthrough) happens inside Reply
Received and is logged in the page body's Email Thread Log with an
`Artifact:` line. Status changes on sends (only after Haytham confirms a
send, as always):

- First send: Audit Ready → Outreach Sent (Touch # = 1, Sequence = Cold).
  The opener carries the #1 finding from the row's `Findings Bank`.
- Cold follow-ups (Touch 2-3, no reply): stays Outreach Sent. Cadence:
  Touch 2 day 3, Touch 3 day 9. After Touch 3 with no reply → Dormant,
  Next Action set 2-3 weeks out. **There is no Touch 4 on this track.**
  Each follow-up must carry something new — see "What each cold touch
  carries" below.
- She replies: → Reply Received, Sequence = Warm.
- The discovery question goes out: → Price Discovery Sent.
- Her answer is logged (verbatim + anchor set) and the priced offer goes
  out: → Offer Sent. **`python main.py crm-gate offer` must print PASS
  before the offer email is even drafted.**
- Call booked / paid: → Call Booked / Won. Explicit no or warm-thread
  ghost after 8-10 touches: → Lost with Lost Reason.

---

## What each cold touch carries (the follow-up payload rule)

A cold follow-up that just bumps is a wasted send and a spam signal — it
eats the day's inbox budget and gives the reader nothing. Every touch on
this track carries a payload, and the send gate enforces it
(`python main.py crm-gate send <row.json> --sends-today N --touch T
--carries X` must print PASS before a follow-up enters the queue):

- **Touch 1:** the strongest verified finding — `Findings Bank` #1.
- **Touch 2 (day 3) and Touch 3 (day 9):** exactly one of
  - `second-finding` — the next UNUSED `Findings Bank` entry (the gate
    checks it exists; never invent one at draft time). Named as a felt
    cost with its innocent explanation, fix left vague — naming a second
    cost is not the Adrienne mistake, teaching a second fix is.
  - `loom-offer` — one line, an offer not a link, no price.
  - `disambiguating-question` — direct binary, no soft exit ("Should I
    stop following up, or is this still on your radar?"). The natural
    Touch 3 closer.

The draft must actually carry what the gate was told (gate.md checks
this). After Haytham confirms the send, the logging step flips the used
bank entry to `USED-TN` in the `Findings Bank` property.

---

## THE PRICE DISCOVERY EMAIL (new email type, this track's whole reason)

**What it is:** one short reply, sent while the thread is warm, that asks
what she'd pay or what's stopping her — BEFORE any number of ours is on
the table. 125 leads and 364 touches produced zero data on why nobody
bought, because nobody was ever asked. This email is the instrument that
fixes that.

**When it goes out:**
- After she's replied, and normally after the turn-two artifact has
  landed (the walkthrough creates the warmth this question rides on).
- If she jumps straight to "how much?" — the discovery question goes in
  the reply BEFORE the number, using the flip shape below, and the price
  follows in the next message as promised.
- NEVER as a response to a stall. If our price is already out and she's
  gone quiet, that's silence handling (mechanics.md + the disambiguating
  questions), not discovery — the unanchored data point is already lost.
  Do not retrofit this question onto a stalled offer.

**When it does not go out:**
- Cold. This is never Touch 1-4 material. A stranger asked "what would
  you pay" replies to nobody.
- Twice. One thread gets one discovery question. If she dodges it, the
  dodge is the data (`Refused to name`).

**The shape:** one real question, answerable in one line, producing a
number or an obstacle. One sentence of setup at most. No price of ours
anywhere in the email. All voice rules apply: proper capitalization, no
em-dashes, no jargon, no weak closers, and it must not read like a survey.

**Canonical phrasings** (pick by situation, adjust wording to the thread —
never paste; the gate's bespoke check applies here too):

1. **Default (artifact landed, moving toward money):**
   > Quick question before I put a number on this. If everything I walked
   > you through got fixed and working by the weekend, what would you
   > expect that to cost?

2. **The flip (she asked "how much?" first):**
   > I'll give you the exact number in my next message, promise. First,
   > out of curiosity, what were you expecting it to cost?

   The promise is load-bearing: it commits to naming the price whatever
   she answers, which is what keeps the question from reading like
   fishing. Keep the promise — the very next message carries the price.

3. **The obstacle read (warm and friendly but non-committal, money never
   mentioned):**
   > Honest question. What would stop you from getting this sorted this
   > month?

   Produces the objection instead of the number. Both are discovery data.

**Logging (this is the study — sloppy logging defeats the track):**
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
- Status → `Price Discovery Sent` when the question goes out (after
  Haytham confirms the send); the answer fields fill when she replies.
- Page body, Price Discovery section: question-sent date, verbatim
  answer, anchor.

**What her answer changes — and what it never changes:**
- It never changes the price. A low anchor is market data, not
  permission to discount. This is hard rule territory.
- It may change WHICH track gets offered (a real-volume operator
  anchoring high might be a Track B conversation).
- A below-anchor answer changes the offer email's emphasis, not its
  number: lead harder with the risk reversal and the guarantee, because
  her anchor says risk is the objection.
- An obstacle answer feeds the offer email directly: the matching bonus
  or term restructure goes in up front (mechanics.md field rules).

**The gate:** before drafting the priced offer that follows, dump the
lead's fresh row to JSON and run `python main.py crm-gate offer
<row.json>`. It fails unless the verbatim answer is logged and the anchor
is set. Quote its literal PASS line when reporting the draft. No PASS, no
offer — take it up with the CRM, not the gate.

---

## Silence handling in this track

Same as mechanics.md, with the corrected lines (the old "no pressure
either way" phrasing is banned like every other weak closer):

- "Are you already handling this, or would it be easier if I took it off
  your plate?"
- "Should I stop following up, or is this still on your radar?"

Direct binary questions. There is always still a concrete thing to say
yes to.

## The daily ceiling

One number for the whole inbox: TOTAL sends leaving it today — openers,
follow-ups, warm replies, both tracks. The ceiling lives in
`send_cap.json` and ramps 20 → 25 → 30 by Haytham's explicit call only
(`python main.py send-cap status` shows the current cap and the ramp
reminder; missing or invalid state fails closed to 20; 30 is the hard cap
for one inbox — more volume means more inboxes). Follow-ups due today eat
the budget first, new openers get what's left — enforced at queue time by
`python main.py crm-gate send <row.json> --sends-today N --touch T
[--followups-due M | --carries X]`. This skill drafts; the uae-tick skill
owns the daily count. If a draft request would obviously blow past the
ceiling (a batch of 30 "for today"), say so and draft for the queue, not
for the day.
