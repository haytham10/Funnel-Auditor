# Decisions

_Written 2026-07-31, seeded from what was already settled across the code, the
journal and the pivot. Everything here has been argued once. The point of the
file is that it does not get argued again by accident._

**Owns:** the decisions that are closed, and the condition that would reopen each
one.
**Defers to:** `docs/journal.md` — the session each decision was made in and what
it cost; `docs/spec/03-offer.md` — the pricing decisions, which are the offer
itself rather than entries here.
**Allows:** none.

## How to read this

Every entry carries **what would reverse it**. That field is what makes this a
decision log rather than a rules list. A decision with no reversal condition is a
preference, and preferences do not belong in a constitution — if you cannot say
what would change your mind, you have not decided anything, you have just gotten
used to something.

Reversing an entry is legitimate. Reversing one *without noticing it was decided*
is what this file prevents.

---

### D1 · The machine never sends
**2026-07-31.** The pipeline ends at a file. Smartlead owns inboxes, warmup,
ramp, sequence steps and replies; Haytham uploads.

**Why.** A pipeline that drafts and sends is one bad batch away from an
unrecoverable mistake across hundreds of real people. A pipeline that drafts and
stops is one bad batch away from a file nobody uploads. The gap between those is
a person reading the preview, and that gap is the product.

**Reversed by** nothing currently foreseeable. If it ever is, the preview gate
has to be replaced by something better first, not removed.

---

### D2 · Never act as Haytham anywhere
**2026-07-31.** No logging in to, acting as, or automating through Haytham's own
accounts on any platform. Read-only, no-login tools only.

**Why.** An identity rule, not a platform ban. Public data through a no-login
third party is fine, on LinkedIn and Instagram the same as anywhere. What is
forbidden is the machine wearing his face.

**Reversed by** nothing. This one is not a trade-off.

---

### D3 · Sell ten names, not a finding
**2026-07-31.** The email offers ten real people who fit the coach's buyer
profile, handed over on a call. It does not offer a diagnosis.

**Why.** The funnel auditor ran 589 leads and made nothing. Its reply rate was
good — 7-9% against a 1-5% benchmark — and **reply to call was 0 of 9.** Two
causes. It sold a finding, and a finding in an inbox is a free fix: 4 of 9
engaged leads read it, fixed it themselves and left. And its call to action was a
question, which selects for replies that are *answers*, and an answer is a dead
end that looks like success.

**Reversed by** a tested offer that beats it on reply-to-call, which is the one
number that has never been above zero. Not by a better reply rate — that metric
is already known to be a liar here.

---

### D4 · `unclear` passes
**2026-07-31.** Every floor verdict is three-valued. Only a clear `no` drops a
row.

**Why.** A false kill is permanent and invisible — the lead is gone and no report
will ever mention it. A false pass costs one research call and gets caught
downstream. Those errors have wildly different prices, so the gate tilts toward
the cheap one.

**Reversed by** research calls becoming expensive enough to matter, which would
mean the fetch ladder had regressed badly.

---

### D5 · A verdict with no source is not a verdict
**2026-07-31.** A hard yes or no on any floor must name what settled it. The
schema rejects it otherwise.

**Why.** An unsourced hard verdict was reasoned rather than fetched. Sourcing it
also makes a `no` arguable instead of something taken on trust, which matters
because of D4.

**Reversed by** nothing. This is the cheapest check in the machine.

---

### D6 · Dedupe before any paid call
**2026-07-31.** Name and domain first, email again after research. A warm-thread
hit stops the run.

**Why.** The previous pipeline deduped last and paid for eight enrichment calls
on an already-excluded lead. And a cold opener landing on a live conversation is
the only failure in this machine that destroys something rather than wasting
something.

**Reversed by** nothing on the warm-hit half. The ordering half is reversed only
if dedupe ever becomes more expensive than research, which would be strange.

---

### D7 · No agent certifies its own work
**2026-07-31.** Every stage making a consequential claim has an independent
verifier that never saw how the claim was reached and defaults to rejecting it.

**Why.** Under the old machine, a third of self-certified findings failed under
scrutiny while carrying a verified flag, and unread citations reached real
drafts. A single context checking its own work is not checking anything.

**Reversed by** nothing structural. The specific instances change as stages do.

---

### D8 · Research gets a schema, not a verifier
**2026-07-31.** Research is the one worker stage with no verifying agent. Its
claims are settled mechanically.

**Why.** A schema check is cheaper than an agent and strictly harder to talk
around. Spend an agent only on claims no regex can settle — whether a quote is
really on a page, whether a paragraph reads like a person wrote it.

**Reversed by** a class of research error the schema demonstrably cannot catch.
Note this is the specific application of a general rule: **prefer a mechanical
check to an agent, always.**

---

### D9 · Never invent a hook, and no hook found is a good answer
**2026-07-31.** A hook is a citation or it is nothing. A hook that cannot be
re-fetched and confirmed means the lead holds and gets no row.

**Why.** A fabricated hook is unrecoverable on the call and it poisons every beat
behind it. There is no volume target that justifies one.

**Reversed by** nothing. Volume pressure is the thing this decision exists to
resist, so volume pressure is not an argument against it.

---

### D10 · The hand-written lines are the anchor, and the linter makes that safe
**2026-07-31.** The drafting model writes against four lines a person wrote. It
may re-voice them so the beats connect; it may not change what they claim.

**Why.** This is the join between the two systems that merged. The cold-email
system had the right copy and a pipeline that stapled beats together mechanically,
so the hook never connected to the paragraph after it. The funnel auditor had a
chassis of fail-closed checks. Giving the model real freedom is only affordable
because everything it could get wrong is mechanically catchable.

**Reversed by** a drafting failure mode that the linter cannot express — which
would be an argument for a better check before it is an argument for less
freedom.

---

### D11 · Never invent a number, and never relabel one
**2026-07-31.** Every number in an email must be true of a real client result.
A number next to a named segment must belong to that segment.

**Why.** Two different failures — invention and relabelling — and either is the
tell that the whole email is fabricated, hook included. The results are real,
they come up on the call, and these coaches compare emails.

**Reversed by** nothing.

---

### D12 · A batch is dealt, not rolled
**2026-07-31.** Anchor lines are allocated across the whole batch at once.

**Why.** Per-lead hashing is unbiased only in the limit and batches are not that
big. Measured on the live lines, a 50-lead batch gave one offer line 8% against a
declared 20% and pushed another over the repetition cap. It converged near n=200.
Dealing gets the worst miss to about a point.

**Reversed by** batches getting large enough that the per-lead draw converges,
which is a change in how the business runs rather than in the code.

---

### D13 · The repetition cap outranks the exact-match ratio
**2026-07-31.** When a segment has too few identity lines to spread its share,
the excess spills to generic rather than putting one sentence in front of most of
a batch.

**Why.** Two coaches comparing notes and finding the same email is worse than one
coach getting a slightly less specific line. The spill is a workaround; the fix
is more lines in that segment, and the deal reports which segments are thin.

**Reversed by** filling the thin segments, which retires the situation rather
than the rule.

---

### D14 · The wall lives in the repo
**2026-07-31.** `data/contacted-before.csv`, not a CRM table.

**Why.** It is read on every run, never needs a view or a filter, and a network
hop is a strange dependency for the cheapest and most consequential check here.
Appending is a commit, so the wall has a history for free.

**Reversed by** the wall growing past what is comfortable to read on every run,
or by a second operator needing to write to it concurrently.

---

### D15 · Firecrawl is gone; the ladder is free-first
**2026-07-31.** Local `requests` and BeautifulSoup, then the agent's own
WebSearch and WebFetch, then Apify for what is genuinely login-walled.

**Why.** Two of the three rungs are free, and the paid rung is batched because
container boot dominates the bill rather than pages.

**Reversed by** the tier-0 fetch rate turning out to be low enough that the free
rungs are mostly wasted work. That number is unmeasured — see
`docs/spec/05-pipeline.md`.

---

### D16 · The audience and price floors were retired, for different reasons
**2026-07-31.** Three floors, not five.

**Why.** The audience floor became irrelevant when the offer changed; the price
floor was relevant but unmeasurable. `docs/spec/02-icp.md` holds both arguments
and the retired number.

**Reversed by** a floor that is *both* measurable and predictive, tested against
both failure modes rather than one.

---

### D17 · The journal starts at the pivot
**2026-07-31.** Everything from 2026-07-18 to 2026-07-30 was deleted, and the
separate archive file with it. Older entries get condensed in place, never moved
to a second file.

**Why.** The deleted log described a machine that no longer exists — Gmail
reconciliations, Loom offers, Notion migrations, a pipeline that was removed.
Three of those blocks loaded at every session start and were actively misleading,
because the hook does not know a pipeline was deleted, it just serves the newest
entries. A hand-maintained overflow file nobody loads is where detail goes to
rot, which is most of what the archive turned out to be.

**Reversed by** nothing. Git has it.

---

### D18 · Documentation is a layer with a gate
**2026-07-31.** `docs/spec/` states decisions and their reasons and holds no
value that something else owns. `python main.py doc-check` enforces the
mechanical half.

**Why.** The previous doc set rotted in three weeks, one reasonable copy-paste at
a time, and cost a commit literally titled *"Sweep the last stale prices and
rename the guarantee everywhere."* One of its five files survived, and it
survived by following this rule before it was written down.

**Reversed by** the gate producing more false alarms than drift, which would be
an argument for narrowing its rules rather than dropping the layer.

**The worked example this decision exists for.** The Apify cost ceiling is a
number, it is genuinely useful in `docs/spec/01-operation.md`, and the file is
forbidden to carry it. There are two ways to comply and only one is right:
declaring an `Allows:` exception is the failure mode wearing a permission slip,
because the number then exists in two places and only one of them can be wrong
without anyone noticing. Naming `audit/apify.py` instead is correct forever and
sends the reader somewhere that cannot lie to them. **When a value is tempting,
that is the signal to point at it rather than copy it.**

---

## What is unknown

- **Nothing here has been reversed yet.** The reversal conditions are untested,
  and a condition nobody has ever met is a guess about what would matter.
- **This file cannot tell a decision from a habit.** An entry nobody has
  questioned in six months may be load-bearing or may be inertia, and reading it
  will not tell you which. The reversal condition is the only handle, which is
  why every entry has one.
