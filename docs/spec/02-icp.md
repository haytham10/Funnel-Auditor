# Who this is for

_Written 2026-07-31. The floors shrank from five to three at the pivot, and the
two that went were removed for different reasons — both recorded below, because
a floor that comes back needs to come back for a new reason, not the old one._

**Owns:** the three hard floors, the decision that `unclear` passes, and which
fields are captured without gating.
**Defers to:** `outbound/qualify.py` — how each floor is actually evaluated and
what evidence satisfies it; `outbound/research.py` — the enum of coach types and
the typed contract every field arrives in; `docs/claude-docs/uae-market-study-2026-07.md`
— the market evidence underneath all of this; `docs/spec/03-offer.md` — every
price, including what this market can pay.
**Allows:** `AED 5,000` — quoted once, as the retired price floor this file
records the removal of. It is not a live number and nothing reads it.

## The floors

Three, and that is all.

| Floor | Means |
|---|---|
| **UAE-based** | based here, not merely serving here |
| **Actually a coach** | coaching is the business, not a line on a consultant's page |
| **Active in the last 30 days** | something they published, dated, inside the window |

`outbound/qualify.py` owns how each is settled and what counts as evidence.
**Activity is 30 days and that number lives here**; the hook's own recency
window is a different question with a different answer, owned by
`docs/hook-rules.md`.

### What each floor can actually reject

Worth stating, because for a while two of the three could not reject anything
and the table above did not say so.

- **UAE-based** kills on a stated foreign residence, and only when that
  sentence is about the lead. A page can say anything about anyone: on the
  first batch a lead was killed by *"based in Singapore"* describing a former
  employer, and another passed on a "dubai" from an unrelated paragraph. Their
  own location field outranks the prose, and prose can produce a `yes` but
  never a `no`.
- **Actually a coach** kills only on a stated non-coach occupation with no
  coach word and no coaching offer anywhere — all three. It used to be
  incapable of rejecting anyone at all: it matched the substring "coach" and
  had no path to `no`, so it was documented as a floor while doing nothing, and
  workers overrode it by hand on cabin crew, a retail supervisor and a
  lecturer. A coach word anywhere is still a pass, including a weekend hobby,
  because separating that from a business needs context the check does not have
  and the error would be the permanent kind.
- **Active in 30 days** kills on a date older than the window. It is the only
  floor that rejects on evidence the machine produced itself, and in practice it
  usually reads `unclear`: on nine real sites and 220,000 characters it found
  zero usable dates, because a copyright year is not activity.

## `unclear` passes

**Only a clear `no` drops a row.** Every verdict is three-valued and every one
carries the source that settled it.

The asymmetry is the entire design, and it is not caution — it is arithmetic.
**A false kill is permanent and invisible: the lead is gone and nothing in any
report will ever say so.** A false pass costs one research call and then gets
caught downstream by a check that can see more. Those two errors have wildly
different prices, so the gate is deliberately tilted toward the cheap one.

The same asymmetry is why a `no` must name its source. A verdict with nothing
behind it was reasoned rather than fetched, and the schema rejects it — so a kill
can be argued with instead of taken on trust.

## The two floors that were removed

Both were reasonable. Both were wrong. Neither was wrong in the same way, which
is why they are recorded separately rather than as "we loosened the gate."

**The audience floor was decoupled from the offer.** The old gate wanted an
audience of at least 1,500. That made sense when the pitch was leverage on their
list. It stopped predicting anything the day the offer became *we will find you
your next client* — that has nothing to do with follower count. The floor did not
get looser; it stopped being about the thing being sold.

**The price floor could not be measured.** About six coach sites in a hundred
publish a number. A floor that reads `unclear` on the overwhelming majority of
the market is not a gate, it is a coin flip with extra fetches attached. The
number it used was `AED 5,000`.

Note the difference: the first floor was measurable and irrelevant, the second
was relevant and unmeasurable. A future floor should be tested against both.

## Captured, never gated

These are collected and stored, and none of them can drop a lead. They exist
because they steer the copy and because they make cohort analysis possible later.

| Field | What it is actually for |
|---|---|
| `coach_type` | **picks the identity line.** The only captured field with a live job. |
| `sells_to` | corporates or individuals — narrows the identity line further |
| `audience_size` | cohort analysis; the retired floor |
| `top_program_price_aed` | cohort analysis; the retired floor |
| `solo` | cohort analysis |

**`coach_type`: LinkedIn wins when the site disagrees.** A website is marketing
copy written once and left alone; a LinkedIn headline is maintained. When they
conflict, the maintained one is the truth.

**`sells_to` is taken from their own words and never inferred.** An empty answer
draws a generic identity line, which is weaker than an exact match and very much
stronger than a confident wrong one. Guessing a coach sells to corporates because
their site looks corporate produces an email that names the wrong reference group
to a real person, and that is unrecoverable in a way "generic" never is.

The type enum lives in `outbound/research.py` and is not restated here — adding a
segment is a code change and a copy change, and a list in this file would just be
a third place to forget.

## What this does not filter on

Worth stating, because their absence is a decision rather than an oversight:
niche, seniority, whether they already do outbound, and whether they look like
they can afford it. The last one is the tempting one, and it is the price floor
wearing a disguise — the market read in
`docs/claude-docs/uae-market-study-2026-07.md` is what to argue with if it comes
back.

## What is unknown

- **Nobody has measured how many UAE coaches this actually describes.** The
  market study estimates a pool and a qualifying share, from one track's
  sourcing. It is one sample, taken before the offer changed.
- **`coach_type` steers the copy and has never been tested against reply rate.**
  It is recorded per lead precisely so it can become a testable variable rather
  than a belief, but that test has not run.
