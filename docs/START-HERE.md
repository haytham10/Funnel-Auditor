# START HERE — the system as it stands

_Last recalibrated 2026-07-28. If you are lost, read only this page. Everything
else is detail you can fetch when you need it._

---

## 1. What you sell, in one sentence

**You sell booked calls to UAE solo coaches.** AED 1,500 setup, credited back
against the first three calls, then AED 600 per qualified call that actually
happens. No retainer, no contract, billing starts at call four.

That is the whole business. Not audits, not funnel fixes, not findings.

## 2. Why it changed (so you stop re-litigating it)

You ran 589 leads and made 0 AED. The pipeline was not broken — it produced a
**9% reply rate against a 1-5% benchmark**. What it never produced was a call:
**reply → call was 0 of 9.**

Two mechanical causes, both now fixed:

1. **A question-shaped CTA cannot produce a booking.** Every opener closed on a
   two-branch question. A question CTA selects for replies that are *answers*,
   and an answer is a dead end that looks like success. → **Every close is now a
   call ask with two specific times.**
2. **A finding in an email is a free fix.** 4 of 9 engaged leads read the
   finding, fixed it themselves and left. A third of findings failed under
   scrutiny while carrying `Finding Verified = YES`. → **The finding never
   appears in an email.** It is reserved call bait: the reason to get on the
   call. The email opens on a *cold read* instead — a measured observation about
   this market that she cannot refute and cannot fix by editing a page.

Nothing ever died on price. Price discovery by email was tested 3 times and
produced 0 numbers. Both dead ends are closed; don't reopen them.

## 3. The email, in five beats

Every cold Touch 1, in this order:

1. **SMYKM hook** — the one line only she would recognise, from real cited
   public evidence (LinkedIn, podcast, YouTube, her About page). Never generic
   marketing copy, never fabricated.
2. **Cold read** — true of most coaches in this market, by measurement, from the
   373-row dataset. Never a claim about her.
3. **Identity beat** — one sentence on who is writing and why he'd know. Without
   it the email reads as someone wanting to buy from her. Two of nine failures
   were caused by this sentence being absent.
4. **The cost** — what the pattern is costing her, vague on the fix.
5. **The call ask** — two specific times. "Tuesday around 4, or Wednesday
   morning, whichever is less annoying."

90-130 words. No em-dashes. No links. No operator jargon. Sign off "Haytham".

## 4. The machine, in one line per stage

Each stage is a skill you fire by name. All four share the same chassis: fan out
workers → an **independent verifier** re-checks the one claim the stage
self-certifies → the orchestrator writes the CRM.

| Stage | Skill | What it produces |
|---|---|---|
| Fill the top | `source-leads` | raw names → `Sourced` |
| Cheap gates | `qualify-leads` | Gate 0 + Gate 1 → `Qualifying` |
| Walk the funnel | `batch-audit` | verified finding **banked** → `Audit Ready` (held, no draft) |
| Hook + draft | `haytham-hook-finder` | verified hook → held Gmail draft → `Draft Ready` |
| You | — | review the drafts in Gmail, send by hand |
| Daily loop | `uae-tick` | replies detected, follow-ups drafted, send queue handed over |

The walk still runs, and the finding still matters — it is just spent on the
call now instead of in the inbox.

## 5. The five things the code will not let you do

You do not have to hold these in your head; they fail closed.

- **No send** without `Finding Verified` **and** `Email Verified`
  (`crm-gate send`).
- **No send over an inbox's daily ceiling**, per inbox, never pooled. 20 → 25 →
  30, one step per 7+ days, your call only. 30 is the hard cap for one inbox;
  more volume means more inboxes.
- **No sends on Sunday**, Dubai calendar day, every inbox, cold and warm.
- **No priced offer** until the lead has earned a number — an earned `Status` or
  `Asked For Price` (`crm-gate offer`). A booked call is the rung that earns it.
- **No bare bump.** Touches 2 and 3 (day 3, day 9) must each carry something
  new: the next banked finding, the call ask, or the disambiguating question.
  Then Dormant.

And two rules only you can keep: **never log in as yourself anywhere**, and
**never send an email from the machine.** It ends at Gmail drafts.

## 6. Which docs to trust

The reason this got blurry: retired offers left their docs behind, and a retired
doc that still claims authority keeps winning arguments after it is dead.

**Canonical — current, load-bearing, believe them:**

| File | What it owns |
|---|---|
| `CLAUDE.md` | the hard rules, the whole map |
| `docs/uae-track/02-the-offer-first-five.md` | the offer, the price, the guarantees, the downsell ladder |
| `docs/uae-track/01-crm-operating-spec.md` | CRM schema, statuses, lifecycle |
| `docs/uae-track/03-targeting-and-sourcing.md` | who to look for, where |
| `docs/uae-track/04-the-outreach-method.md` | the motion, the walk, the sequence |
| `.claude/skills/haytham-email-draft/references/` | `cold-reads.md`, `mechanics.md`, `uae-track.md` — the actual copy spec |
| `docs/journal.md` | what happened, newest first |

**Advisory — real evidence, but they are studies, not instructions:**
`docs/claude-docs/uae-market-study-2026-07.md`,
`docs/claude-docs/nine-threads-and-phase10-correction.md`,
`docs/claude-docs/outreach-system-vs-saraev-comparison.md`.

**Historical — do not work from these:**
`docs/claude-docs/fix-list-final.md` (consumed, shipped),
`docs/claude-docs/saraev-translation-a-to-z.md` (partly refuted by its own
header), `docs/claude-docs/offer-the-first-five.md` (superseded by the repo copy
at `docs/uae-track/02-the-offer-first-five.md`), `docs/journal-archive.md`.

**Rule of thumb for anything in your Claude project:** if a doc names a price
that is not 1,500 / 600, or tells you to put a finding in an email, or asks a
lead what they'd pay — it is dead. Those three tells catch nearly every stale
document you have.

## 7. What is actually still unknown

Be honest about the open bet, because it is the only thing that matters now:

- **No call has ever been booked, for anyone.** The call-ask CTA is one week
  old. It has never been tested at volume.
- **The delivery math is unproven.** Five calls in 30 days needs roughly one
  reply in seven to book. Plausible — the CTA has never once asked — but it is a
  bet, and Five or Free means you carry it.

So the single number to watch is **reply → call.** Everything upstream already
works. If that number moves off zero, you have a business and a proof asset. If
it stays at zero after a real sample, the problem is upstream of the CTA and you
will know where to look next.
