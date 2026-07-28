# Cold reads — the opener's beat 2

**v2, 2026-07-27.** Rebuilt after the First Five pivot. The v1 list was written
against the *old* offer and it shows: `price-invisible`, `no-aed` and
`price-band` are all observations about how she displays a price. That was the
right beat 2 when the thing being sold was a funnel fix. It is a non-sequitur
now. **The offer sells booked calls. The cold read has to be about the empty
calendar, not the price tag.**

A prospect reads beat 2 and beat 5 as one sentence. If beat 2 is "your price
isn't visible" and beat 5 is "let me book calls for you," she has to build the
bridge herself, and she will not bother.

## The rule that did not change

A cold read is a statement about the **market**, true **by measurement**, that
she cannot refute and cannot fix by editing a page. That is the safety property
and it is the whole design. Findings stay `RESERVED` call bait and are never
emailed at any touch, in any form.

## The rules

- **Rotate.** One pattern per prospect. Vary the phrasing every time.
- **Never invent a pattern.** Not on this list, not in an email.
- **Never name her as the one with the problem.** "Most coaches here…", not
  "you don't…".
- **No number that is not on this page** or on the credibility list in
  `mechanics.md`.
- **Declare it to the gate.** `crm-gate send --touch 1 --cold-read <id>`.
- **Every pattern below must terminate in an empty chair.** If you cannot get
  from the cold read to "and that is a call that did not happen" in one
  sentence, it is the wrong pattern for this offer.

Source for every stat: `docs/claude-docs/uae-market-study-2026-07.md`.

---

## `half-empty-week` — the strongest on the list

**Stat:** ICF measured average coach revenue $49,283/yr on **11.6 working hours
a week across 12.4 clients**; first year $14,484. (market study, purchasing-power row)

> The coaches I go through here are working about eleven and a half hours a
> week, across twelve or so clients. That is not a small practice. That is a
> practice with room in it.

**Why it leads the list:** it is the only pattern that lands directly on the
thing being sold. Beat 4 writes itself, and it flatters rather than accuses:
the implication is that the work is good and the week is not full, which is a
supply problem, not a competence problem.

**Cost line pairs with:** the hours that are already paid for and already empty.

---

## `agency-burn`

**Stat:** coach-marketing agencies charge AED 7,300–22,000/month. The loudest
complaint across every source is non-delivery, not price. Verbatim from
r/lifecoaching: *"I'm so frustrated with coaches approaching me wanting to help
me market, if I pay them 5000 to 10,000 dollars."* And: *"appointment setting
agencies charge $4-10k/month whether they deliver or not."*

> Nearly everyone selling marketing to coaches here charges somewhere between
> seven and twenty-two thousand dirhams a month, and charges it whether anything
> lands or not. The complaint I read most often in this market is not that it
> was expensive. It is that nothing arrived.

**Why it works:** it pre-frames the price structure before the price exists. By
the time she hears "you pay per call that happens," the contrast is already
built. This is the pattern to use when the walk shows she has clearly been sold
to before (an agency-built site, a template she is paying for, a GHL install).

**Cost line pairs with:** money already spent on a month where nothing arrived.

⚠️ Never name a specific agency and never imply you know who she used.

---

## `audience-decoupled`

**Stat:** audience size and price ceiling are close to uncorrelated. AED 18,400
per corporate workshop off 268 followers; 330,000 followers monetised by one $29
course. (`:47`)

> Audience size and what people actually charge here have almost nothing to do
> with each other. The best per-session number I have come across came off 268
> followers. The biggest following I have come across sells one twenty-nine
> dollar thing.

**Why it works for this offer:** it moves the conversation off "grow the
audience" and onto "fill the week," which is the only move the offer can make
good on. Strongest non-accusatory read on the list. It flatters small audiences
and reframes large ones without blaming either.

**Cost line pairs with:** the effort going into a number that is not the
constraint.

---

## `rented-audience`

**Stat:** 36 of 87 walked leads with an audience-ownership verdict (41%) have no
email capture of any kind. (`:36`)

> Most coaches here have no way to reach the people who looked and did not book.
> They are all on the other side of something nobody owns, and every launch
> starts from nothing again.

**Framing is load-bearing.** Write it as a *felt cost* ("the people who looked
and didn't book have no way to hear from you again"), never as a missing
mechanism ("you have no email capture"). The vitamin filter is unchanged:
mechanisms do not convert cold.

**Cost line pairs with:** the person who was ready in March and is unreachable
in July.

---

## `platform-tenant`

**Stat:** 28 disqualified leads have a marketplace as their only commercial
presence; 21 of 89 are a third-party directory or marketplace listing only.
(`:26`, marketplace paragraph)

> A lot of the coaching businesses I go through here only really exist inside
> somebody else's marketplace. The booking, the profile and the customer all
> belong to the platform. It works right up until the platform decides who gets
> shown that week.

**Use when:** the walk found her on Skilldeer, iheal, Playbook, a directory, or
any third-party as the primary commercial path.

**Cost line pairs with:** a week where the platform showed someone else.

---

## `optimism-gap`

**Stat:** MEA leads the world on every ICF sentiment measure. 71% expect revenue
growth, 72% expect more clients, 62% expect more sessions. Measured average coach
revenue is $49,283/yr.

> Coaches in this region are the most optimistic in the world on every measure
> anyone tracks. Seven in ten expect more revenue this year and seven in ten
> expect more clients. Almost nobody I read has a written-down way that the
> second one happens.

**Weakest of the six.** It is true and it is measured, but it is closer to a
lecture than the others. Use it when nothing else fits, and cut it to two
sentences.

**Cost line pairs with:** a year of expecting, ending the same size.

---

## Retired from v1 — do not draft these under The First Five

| Pattern | Why it is gone |
|---|---|
| `price-invisible` | 48 of 122 show no visible price. True, measured, and about the wrong problem. It sets up a conversation about her pricing page and this offer does not touch her pricing page. Restore it only if a pricing offer ever returns. |
| `no-aed` | Same. A currency observation is a funnel-copy note, not a reason to take a call about a booked calendar. |
| `price-band` | Same, plus it only works when her pricing is visible, which is the minority case. |

They stay in this file as a record, not as a menu. The gate list drops to the
six above.

## Still not shipping: `call-centric` and `waiting-room`

`call-centric` — *"46 of 122 walked leads have a free discovery call as the only
way in"* — is still unsourced. The 46 appears only in the offer spec; the market
study has no 46. The nearest measured figure, 32, is drawn from the **disqualified**
population, a different denominator.

`waiting-room` — *"most coaches here only get found by people already looking
for them"* — is the pattern this offer most wants to own, and there is no count
behind it at all yet.

**Both need a fresh CRM count before they exist.** They are the two highest-value
gaps on this page: get the numbers.
