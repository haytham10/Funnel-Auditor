# The Offer — The First Five

Current pricing and offer structure for the UAE track. Decided 2026-07-27,
**repriced 2026-07-28.** Supersedes all earlier pricing. If a number anywhere
else contradicts this, this wins.

**We sell booked calls.** Not a funnel, not a fix, not an audit.

> **Repriced 2026-07-28 to AED 2,000 setup + AED 900 per qualified call, no
> credit-back, billing from call one.** The v1 numbers (1,500 credited against
> the first three calls, then 600) were wrong in two ways that were measured,
> not argued:
>
> 1. **AED 600 is $163.** The market study prices this category at $150-300 for
>    basic (a name and a slot), $300-500 for ICP-matched, and $400-750 for
>    BANT-verified with no-show replacement. We deliver the top band — written
>    openers, a price-first filter, a no-show guarantee — and charged below the
>    bottom of basic. Being the cheapest is not a moat, it is a race won into
>    poverty.
> 2. **The credit-back was a discount wearing a guarantee's clothes.** A client
>    taking five calls paid 1,500 + 2 x 600 = 2,700 in month one; one taking
>    three paid 1,500. That gave away AED 1,800 of month-one cash for a
>    concession Five or Free already buys. Never discount, add value instead.
>
> **The `price never moves` rule was not violated by this change.** That rule
> exists so a reprice cannot destroy the read on a running test. There is no
> test running and there are zero closes, so there was no read to protect. Set
> the price right BEFORE client one; after that it is a conversation with an
> existing customer. It is frozen now until two clients are delivered.

---

## What this replaced, and why

> **Retired 2026-07-27: the funnel-fix offer (Grand Slam Offer v2).** Track A
> (735 AED / $200), Track B (2,575 AED / $700, "The Booked-Out Funnel"), the
> 500 AED 48-Hour Leak Fix, the free Loom, price discovery as an email step,
> the 3,600 AED next price step, and the Live-or-Free / First Booking
> guarantees. All gone. Do not reinstate any of them.
>
> This file used to assert that those numbers were canonical and outranked
> every other doc in the repo — which is exactly why it is overwritten rather
> than deleted. A retired offer that still claims authority keeps winning
> arguments after it is dead.

Not because the machine failed. Because the thing it sold could not be sold:

- **Leads fix findings themselves.** 4 of 9 engaged leads consumed the finding
  and left. Avneet: *"Ive fixed most of it. Incase anything else stands out let
  me know."* Rita fixed her booking flow and swapped to Calendly. The finding
  was small enough that naming it WAS fixing it.
- **A third of findings did not survive contact.** 3-4 of 9 engaged leads had
  the finding fail under scrutiny. All carried `Finding Verified = YES`.
- **Nothing ever died on price.** 3 price-discovery answers, all `Refused to
  name`, two of three asked us for a number instead.
- **Zero revenue across 589 leads.** 373 UAE + 194 parenting + 22 legacy.
  0 calls, 0 closes, 0 AED.

The mechanical cause of 0 calls from 9 replies: **a question-shaped CTA is
optimised for reply rate and structurally cannot produce a booking.** We got
exactly what we asked for — 9% replies and zero calls.

---

## The market

**UAE-based solo coaches and practitioners with a live program priced at AED
5,000 or above, and a calendar with room in it.**

*(Re-niched 2026-07-28, up from "a live paid offer at AED 1,500+".)* The market
study's purchasing-power indicator is a measured FAIL: ICF puts average coach
revenue at $49,283/yr and most UAE coaches sit under the AED 375,000 VAT line.
The old answer was to price low enough for a broke market to afford, which is
solving a targeting problem with a discount. This is the other answer.

The arithmetic only works above the floor. A coach with an AED 8,000 program
closing one in four takes AED 2,000 per call taken and pays 900 for it. A coach
with an AED 800 program cannot make that work at any price we could charge, so
a reply from her was never revenue.

**Enforced, not aspirational:** Gate 0 has a fifth floor
(`audit/gates.py`, `PROGRAM_PRICE_FLOOR_AED`). It reads her HIGHEST live
program, not her cheapest workshop.

---

## The dream outcome

**A week that fills itself. Thirty days from now, people who already know what
you charge are booking time with you, and you did not chase, post or DM anyone
to make it happen.**

*(Rewritten 2026-07-28.)* The old version — "qualified discovery calls on your
calendar" — is a METRIC, and one she cannot bank. It also invites the only
objection that matters, "and what if none of them buy?", while giving nothing to
answer with. The destination is the WEEK. The qualifier "already know what you
charge" rides in as a benefit rather than a feature, and "without posting,
DMing or chasing" states the effort driver as part of the promise.

---

## The stack

| Problem it kills | Component | Value |
|---|---|---|
| "I don't know who to target" | **The Client Mirror** — ICP built backwards from their own best-paying clients | AED 1,800 |
| "Nothing will happen for weeks" | **The 48-Hour First Draft** — the list, the profile and the first twenty openers on her desk within two days of go, before a single email sends | AED 2,000 |
| "I don't have their details" | **The Named List** — verified, deliverable, gate-checked contacts | AED 2,400 |
| "You'll burn my domain" | **The Clean Domain Shield** — separate sending domain, warmed, SPF/DKIM/DMARC. Their main domain untouched | AED 3,000 |
| "I hate sounding salesy" | **The Written Opener** — every message built on something real about that specific person | AED 3,600 |
| "I'll get tire-kickers" | **The Price-First Filter** — prospects told what they charge before a call is booked | AED 1,200 |
| **"A booked call isn't a client"** | **The Call Brief** — a one-page read on each person before she speaks to them: what they sell, what they said, what they are likely to want | AED 2,400 |
| "They book and don't show" | **The Show-Up System** — confirmation and reminder sequence | AED 1,200 |
| "What about the ones who didn't book" | **The Objection File** — every reply that wasn't a yes, sorted, so she learns what her market actually pushes back on | AED 1,500 |
| "Agencies take my money and go dark" | **The Weekly Read** — what went out, what replied, what booked, what's changing | AED 900 |
| **Stacked value** | | **AED 20,000** |

**The Call Brief is the component that ends the commodity comparison.** An
appointment setter hands over a name. We hand over a page on who they are,
because we have walked 373 of these businesses and nobody else in this market
has. It is the only item on the list a competitor cannot copy this quarter.
Lead with it.

**The 48-Hour First Draft is the time-delay fix.** Time delay was the weakest
driver in the Value Equation by a distance — 30 days to the promise with three
weeks of it invisible. Something real lands on her desk in two days.

---

## The price

**AED 2,000 to set up. Then AED 900 per qualified call that actually happens.
Billing starts at call one.**

No retainer. No contract. No minimum term. **No credit-back — setup is
revenue.**

At $245, AED 900 sits mid **ICP-matched** tier in a category we deliver above.
This is still not a premium price. It is an honest one.

The comparison the prospect makes for themselves: appointment-setting agencies
charge **AED 7,300-22,000/month whether they deliver or not.** A coach with an
AED 8,000 program closing one in four takes AED 2,000 per call taken and pays
900. At one in three, AED 2,667 against 900. The `agency-burn` cold read
pre-loads exactly this comparison.

**Value-to-price gap:** AED 20,000 stacked against AED 2,000 to start.

**The price holds until two clients are delivered.** Raise in stages, never
discount, add value instead. A low anchor from a lead is market data, not
permission to discount.

**Retired, do not quote: 735 / 2,575 / 3,600 AED, and the v1 First Five numbers
1,500 setup / 600 per call.** AED 500 is no longer retired — it is the price of
The Named Fifty, the attraction offer (`05-the-named-fifty.md`).

---

## THE GUARANTEES — both, named, stacked, unprompted

Risk is the #1 objection and the market brief's own conclusion is that the
blocker is trust. Both go in every money email, stated boldly before any
objection arrives, by name:

1. **The Empty Chair Guarantee** (performance, type 4) *(renamed from "The
   No-Show, No-Charge Guarantee" 2026-07-28 — same promise, a name that says
   what it protects)*:
   > You pay for seats that get filled. If she doesn't show, you don't pay.
   > Cancellations, no-shows and people who turn out not to be your buyer are
   > my cost, not yours.

2. **Five or Free** (conditional, type 2 — upgraded from refund to SERVICE
   2026-07-28):
   > Five qualified calls in your first thirty days **of sending**, or the
   > setup comes back **and I keep sending free until you have five**. You keep
   > the domain, the warmed inboxes, the list and the copy either way. All I
   > ask is that you take the calls and get me access in the first week.

   Three things changed, each load-bearing:

   - **"Of sending", not from payment.** Warming a fresh domain to safe volume
     takes two to three weeks. With the clock starting at payment, Five or Free
     was close to unwinnable as written and Haytham was the one holding that
     bet. The clock now starts at first send. Say it plainly, so it reads as
     precision rather than as a get-out.
   - **"I keep sending free until you have five"** — a service guarantee beats
     a refund: it removes the time risk instead of just repaying the money, and
     it costs time rather than cash.
   - **A client-side condition.** "Take the calls and give me access in week
     one." Without it she can disappear for thirty days and still claim.

Type 4 (performance/implied) stacked with type 2 (conditional). This is
deliberate: with zero case studies, perceived likelihood is the binding
constraint, and a performance structure makes it nearly irrelevant. Max downside
per failed client: AED 1,500 refunded plus one month of send capacity.

**The condition on ② is load-bearing** and is never dropped to sound generous.
It bounds the promise to a window and a number; without it the guarantee is
unbounded and reads as desperate.

---

## Scarcity and urgency — both honest

**"I run four of these at a time."** Arithmetic, not tactics: each client needs
its own sending domain, its own slice of the daily ceiling, and every opener is
written by hand. State the real number; it doubles as proof this isn't
spray-and-pray. **And say how many are taken** ("two of the four are gone") —
stated capacity doubles as social proof and is the most honest form of scarcity
there is. Only ever say the true count.

**Urgency, cohort-rolling:** onboard on the 1st and the 15th only. Real, dated,
honoured. A rolling deadline you actually keep costs nothing and never expires.

**Every money email carries exactly one true scarcity line. Not two, and never
invented.** GSO v2 registered honest scarcity in two places and shipped it zero
times across every sent email in the repo — the lines existed and were never
said. Do not let that repeat.

---

## The name

**"The First Five — a 30-Day Booked-Calendar System for UAE Coaches"**

M-A-G-I-C audit of the previous wording ("30 Days to a Booked Calendar, for UAE
Coaches"): Avatar ✓, Goal ✓, Interval ✓, Magnet ✗, **Container ✗** — so the
container word ("System") is added and nothing else changes. Keep "The First
Five": it is memorable, it matches the guarantee, and churning a name you just
shipped is motion, not progress.

Alternates worth testing later, not now: **"Five Chairs, Thirty Days"** ·
**"The Full Week Intensive."**

---

## The three laws (carried over — these were right)

**1. Make it instant and effortless, not just impressive.**
Value = (dream outcome x likelihood) / (time delay x effort). Big claims are the
crowded half. The winnable half for a solo operator is the bottom of that
fraction.

**The friction sentence, in every money email:**
> All I need from you is about twenty minutes at the start. After that you do
> not hear from me until there are calls on your calendar.

Costs one sentence and kills the objection that three separate frameworks
independently flagged as unaddressed.

**2. Risk is the whole objection.**
Every question a cold lead asks ("what does it cover", "where are you from",
"show me your work") is one question wearing three hats: *is this real*. So the
offer leads with risk reversal, not with deliverables. State the worst case
unprompted, boldly, before they object.

**3. The price never moves.**
A collapse teaches the lead the price was fiction. Three legal moves when they
stall, none of them a discount:
- Stall on value → add a **bonus** matched to the stated obstacle
- Objection to a **term** → restructure the term (deposit, timing, payment)
- Objection to **scope** → unbundle

---

## THE DOWNSELL LADDER — never drop the price for the same thing

"The price never drops, the scope does" is law, but without a named ladder it
resolves in the moment, which is exactly when people cave. Standing rungs,
worked in order:

1. **Fewer Calls** — commit to three instead of five; setup drops to AED 1,200,
   the per-call rate stands at 900. Less product for less money, which is a
   feature downsell, not a discount. First rung on any "it costs too much",
   because that objection almost always means "it costs too much before I see
   anything."
2. **Setup Deferred** — no setup fee at all, AED 1,250 per call instead of 900.
   She pays only for outcomes and the premium covers the risk we carry, so the
   total is HIGHER, not lower. Changes the payment structure, never the value.
   Delays cash, so never the opening move.
3. **The 1-10 check, only after two downsells** — "how badly do you want the
   calendar full, 1 to 10?" 8 or above goes on rung 1. 7 or below means
   recombine to whatever their 10 actually is, or let it go. This is not an
   offer, it is a diagnosis before conceding anything.

Never skip to rung 3, never stack two rungs in one email, never invent a rung.
A rung is a different deal, not a cheaper one.

---

## The two open risks, stated plainly

**The delivery math is unproven.** At 15 sends/day and a 7.4% touch-1 reply
rate, a month for one client is ~450 sends → ~33 replies → unknown calls.
Reply-to-call has been 0 of 9. Five calls in 30 days needs roughly one reply in
seven to book. Plausible — the CTA has never once asked for a call — but it is a
bet, and Five or Free means Haytham carries it. **Now a SERVICE guarantee, so a
miss costs sending time rather than the setup fee**, which is the cheaper way to
be wrong.

**Volume is a fifth of the floor, and that is the largest uncapped lever.** The
Rule of 100 floor is 100 primary actions a day; we run 15-50 sends across two
inboxes. This cannot be fixed by sending more per inbox — that is the one lever
that breaks deliverability, and the ceiling is 30 per inbox for exactly that
reason. It is fixed with MORE INBOXES: four to five warmed inboxes at 20-25/day
each. Everything else in this document is a percentage improvement on a base
that is five times too small. **More, then Better, then New** — and GCC
expansion is a New move that stays parked until the first two are exhausted,
which they are nowhere near.

**No call has ever been booked, for anyone.** Mitigation: run both at once.
Point the machine at Haytham's own pipeline with the new call-asking CTA while
pitching the offer to the live warm threads. Same machine, two purposes. The
moment his own calendar has calls on it, the proof asset exists.

---

## Field rules (so this survives contact with a live thread)

1. **The price never drops.** Bonuses answer stalls. Term restructures answer
   term objections. Unbundling answers scope objections. The named downsell
   ladder answers "too expensive". Four different moves, none of them a
   discount.

2. **Risk reversal goes first, boldly, before she objects — and that means BOTH
   guarantees, by name.** The No-Show No-Charge Guarantee and Five or Free
   (with its 30-day condition), stacked, in every money email. "State a
   guarantee" is not enough instruction; say which. Naming the worst case
   unprompted ("the most this can cost you is nothing, and you keep everything I
   built") is the strongest line in the arsenal.

3. **Proof rides with every offer.** She must be able to verify in 30 seconds
   that I am real, because that is the actual question she is asking.

4. **Numbers stay straight. Blur them once and the whole proof layer dies:**
   - **$8,123** and **+93%** belong to **Birds & Bees** (single 7-day launch,
     Dec 2025, one product, no email campaign, her best ever)
   - **$522** and the **1-in-4 take rate** belong to **Screen Smart order bumps**
   - **6.6% conversion** belongs to the **Hijab Workbook** (~3x the ~2% industry
     average)
   - 4x 5-star Upwork reviews

   All from Peace Within Home, which came **INBOUND**. It proves delivery
   quality and retainer growth. It does NOT prove a cold-outreach method. Never
   present it as cold-outreach proof.

---

## The gate

**The lead must have EARNED a number before this offer goes out.** `python
main.py crm-gate offer <row.json>` must print PASS: an earned `Status` (`Call
Booked`, `Offer Sent`, `Won`, or the legacy `Leak Fix Sold` / `Leak Fix
Delivered`) or the `Asked For Price` checkbox. See the CRM spec.

**The gate has two tiers as of 2026-07-28.** This offer is the `core` tier and
is the default, so nothing above changes. The AED 500 Named Fifty is the
`attraction` tier (`--tier attraction`) and needs only a live thread, because an
attraction offer exists to buy a customer and the earned right would make it
unsendable. Pick the tier by which offer you are drafting, never by which
verdict you want.

**A booked call is now the rung that earns the number** — which is the whole
point of the offer. The old ladder needed a paid tiny yes to get there; this one
sells the call itself, so `Call Booked` and the earned-right gate finally
describe the same event.

The rule was never "know their budget before quoting." What was **falsified on
2026-07-24** is that you can ask: across 100 touched leads the question went out
3 times and produced 3 answers, all `Refused to name`, and 0 numbers. Two of the
three refusers responded by asking us for a price instead. Nobody names a budget
to a stranger over email, and the refusal turned out to be a trust signal, not a
price signal — so the answer to it is more risk reversal, never a smaller
number. `Price Discovery Answer` and `Discovery Anchor` stay in the CRM as
advisory data. Their anchor does not change the price. It is market data.

---

## UAE-specific note

Prices are quoted natively in AED. Do not quote two currencies at a lead in the
same breath, and never present the AED figure as a discount or a conversion.
