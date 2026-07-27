# Cold reads — the opener's beat 2

**The opener is no longer a finding.** (Changed 2026-07-27.) Beat 2 of the cold
Touch 1 is a *cold read*: an observation that feels personal but is true of most
coaches in this market, and is true **by measurement** — every pattern below is
counted from the 373-row UAE dataset, not guessed.

## Why the finding stopped opening emails

Two reasons, both paid for:

1. **Proving she wants more booked calls is worthless.** Every coach wants that.
   A finding spends the whole email establishing something she already knows.
2. **A finding that turns out wrong, or that she fixes herself, costs more than
   silence.** 4 of 9 engaged leads consumed the finding, fixed it and left
   (Rita's booking redirect, Avneet's test-SKU checkout). A third of findings
   failed under scrutiny while carrying `Finding Verified = YES` (Lisa,
   William). Both failure modes are *impossible* with a cold read, because a
   cold read makes no claim about her specifically.

**That last point is the safety property, and it is the whole design.** A cold
read is a statement about the market. She cannot refute it, and she cannot fix
it by editing a page. If she disagrees, she disagrees about coaches in general,
which is a conversation, not a correction.

**Findings are now RESERVED call-bait only.** They are never emailed — not as an
opener, not as a second-finding, not as a teaser. They are the reason to get on
the call.

---

## The rules

- **Rotate.** One pattern per prospect. Vary the phrasing every time — the shape
  is fixed, the wording is not, and a cold read reused verbatim is a tell the
  second time it ships.
- **Never invent a pattern.** If a cold read is not on this list, it does not go
  in an email. Same discipline as "never invent findings" — this list is the
  bank.
- **Never name her as the one with the problem.** "Most coaches here…", not
  "you don't…". The moment it becomes an accusation about her specifically it
  is a finding again, with all the risk back.
- **No number that is not on this page** (or on the credibility list in
  `mechanics.md`). Every figure below carries its source; if you cannot point at
  the source line, it does not ship.
- **Declare it to the gate.** `crm-gate send --touch 1 --cold-read <id>` — the
  gate validates the id against this list, same declare-what-you-drafted
  discipline that used to apply to `--opener-rank`.

Source for every stat: `docs/claude-docs/uae-market-study-2026-07.md`
(490 currency amounts parsed from 88 priced leads; 122 full funnel walks;
373 rows found in 14 days).

---

## `price-invisible`

**Stat:** 48 of 122 walked leads show no visible price anywhere. (`:34`)

> Most of the coaching sites I go through here never put a number on the page
> anywhere. The thinking is usually that price is a conversation, not a
> billboard. What it does in practice is make the first message you get be "how
> much," from people who were never going to pay it.

**Cost line pairs with:** the time spent answering price questions from people
who disqualify themselves one email later.

---

## `no-aed`

**Stat:** 49 of 88 priced leads use no AED at all. Of 490 amounts: USD 312, AED
148, GBP 20, EUR 10. (`:65`)

> More than half the coaches pricing UAE work here quote in dollars. It reads
> normal from the inside, because that is how the industry talks. To someone in
> Dubai deciding in about four seconds whether this is for her, it quietly reads
> as "this is not local."

**Cost line pairs with:** the buyers who never write, so you never hear about it.

---

## `price-band`

**Stat:** median program AED 1,831; median session AED 894; the distribution is
bimodal, with a low-ticket mass under AED 500 and a distinct AED 1,000–2,500
band. (`:57-63`)

> The middle of this market sits at about 1,800 for a program and 900 for a
> session, and almost everyone lands inside that band whether their work belongs
> there or not. The band is where the market's default lives, not where anyone
> decided to be.

**Cost line pairs with:** being priced by the market's habit rather than by the
work. Use only when her pricing is genuinely visible — otherwise it reads as a
guess.

---

## `audience-decoupled`

**Stat:** audience size and price ceiling are close to uncorrelated. AED 18,400
per corporate workshop off 268 followers; 330,000 followers monetised by one $29
course. (`:47`)

> Audience size and what people actually charge here have almost nothing to do
> with each other. The highest per-engagement number I have seen came off 268
> followers. The biggest following I have seen sells one twenty-nine dollar
> thing.

**Cost line pairs with:** the effort going into growing a number that is not the
constraint. Strongest non-accusatory read on the list — it flatters small
audiences and reframes large ones without blaming either.

---

## `rented-audience`

**Stat:** 36 of 87 walked leads with an audience-ownership verdict (41%) have no
email capture of any kind — 19 with zero capture, 17 with only a contact or
booking form. (`:36`)

> Most coaches here have no way to reach the people who looked and did not book.
> They are all sitting on the other side of a platform nobody owns, and every
> launch starts from zero again.

**Framing is load-bearing on this one.** It must be written as a *felt cost*
("the people who looked and didn't book have no way to hear from you again"),
never as a missing mechanism ("you have no email capture"). That is the vitamin
filter's own worked example of the difference (`haytham-opener-finder/references/walk.md`),
and the filter is unchanged: mechanisms do not convert cold.

---

## Not shipping: `call-centric`

The intended sixth pattern — *"46 of 122 walked leads have a free discovery call
as the only way in"* — **is not on this list because it could not be sourced.**

The figure 46 appears only in the offer spec, unsourced, and the market study
that spec names as its evidence base contains no 46 at all. The nearest measured
figure is "own site, free-call / contact-form only, no price, no checkout — 32",
which is drawn from the **89 disqualified** leads (`:26`), a different and
opposite population; applying it to qualified leads would be dishonest.

The observation is probably true and is worth having — it needs a fresh count
from the live CRM before it can be written into a cold email. Do not ship it
from memory.
