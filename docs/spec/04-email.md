# The email

_Written 2026-07-31. The copy survived the pivot; the pipeline around it did not.
What is new is that the hand-written lines became the drafting model's anchor,
and a deterministic linter made that safe._

**Owns:** what one email is — the beats, their order, the word budget, the
anchor contract, and the copy rules.
**Defers to:** `docs/hook-rules.md` — beat 1 in full, which is the only beat
written from scratch; `copy/identity.csv`, `copy/offer.csv`, `copy/cta.csv`,
`copy/ps.csv` — the hand-written lines themselves; `copy/results.csv` — the
client results every number traces to; `outbound/lint.py` and
`audit/draft_lint.py` — the checks as implemented; `outbound/anchors.py` — the
line draw and the fact table; `docs/spec/03-offer.md` — every price, none of
which may appear here.
**Allows:** none.

## What one email is

Five beats, **67 to 95 words**, plain text. No links, no attachments, no price.
Signed **Haytham**.

Short is not a style preference. The email is asking for fifteen minutes from
someone who did not ask to hear from us, and every sentence past the fourth is
an argument for deleting it.

**Counted on the assembled body**, which includes the greeting and the sign-off,
by one function — `lint.word_count`. There were briefly two counters, and they
disagreed by a word on any figure carrying a separator, in the direction of a
guard passing a combination the linter then refused.

### The hook pays

Four of the five beats are drawn, so the hook is the only beat that absorbs a
long draw. `lint.MIN_HOOK_WORDS` is the floor: twelve words is a short hook but
a real one.

**A long line is not the problem. A long *combination* is.** This used to be
enforced against the copy — the longest line in every beat had to be able to
coexist, so one 27-word identity line could fail the whole bank and the only fix
on offer was to trim a hand-written sentence until it read like a machine wrote
it. For a combination nobody had to be dealt: six of the live bank's 2,112 were
ever too tight.

So the constraint moved to where the combination is actually chosen. **The deal
does not issue a set of lines with no room for a hook** — it swaps the ps, or
the ps and the cta, exactly as it already does when two beats repeat a phrase.
The lines are never edited. Identity never moves, because it is matched to the
lead's segment and that match is the thing the 70/30 ratio exists to buy.

What is still checked against the copy is the one failure a swap cannot fix: a
line so long it can never be dealt with *any* partner set. That line is dead —
it draws a weight and never reaches a reader.

The drafter is handed its actual hook budget per lead rather than discovering it
by rejection. A drafter that knows it has fourteen words writes fourteen; one
that does not writes twenty and gets refused for length.

## The beats, and why the order is fixed

Each beat answers the objection the reader raises at that exact moment. Reorder
them and a beat answers a question the reader has not asked yet, which reads as a
non sequitur even when every sentence is individually fine.

| # | Beat | The objection it answers |
|---|---|---|
| 1 | **Hook** | *is this a spammer?* |
| 2 | **Identity** | *who is this and why should I care?* |
| 3 | **Offer** | *what can you do for me?* |
| 4 | **Close** | *what happens next?* |
| 5 | **ps** | *what does saying no cost me?* |

Assembled as hook, identity, offer, close, sign-off, ps — the order is fixed in
`outbound/export.py` and changing it changes every email in the campaign at once.

**Hook** — one or two sentences about something specific and recent they did,
cited, plus a clause saying what you took from it. `docs/hook-rules.md` owns this
beat entirely: the four requirements, the twelve bans, where hooks come from in
cost order, and why an independent agent verifies it.

**Identity** — a matched reference group, a real number, a timeframe. **It must
turn to the reader before its first digit.** An identity beat that opens on
Haytham's numbers is a CV; the same numbers after "your next client is the job"
are evidence.

**Offer** — ten names, already pulled. Not a promise to pull them.

**Close** — fifteen minutes, a clock on the deliverable, and why these ten and
not the other forty. **The close must keep its second half.** A close that loses
the reason only a conversation can answer becomes a question, and a question
selects for replies that are *answers* — which is a dead end that looks like
success. That is how reply-to-call went zero for nine.

**ps** — a costless no. It is not a throwaway; it is the beat that makes not
replying cheap, which is what makes replying honest.

## The bridge

The single most common failure, and the one that cannot be repaired downstream.

**The hook must have a writer in it.** Compare:

> You wrote that you couldn't contain the excitement of uncovering a solution for
> yourself.

> You wrote that you couldn't contain the excitement of uncovering a solution for
> yourself. That is a strange thing to read from someone who sells the solving.

The first hands them back their own sentence and stops. The second has a person
in it, and the identity beat now has somewhere to start from. A hook with no
writer produces an identity beat that reads as a non sequitur **whatever that
beat says** — which is why no amount of rewriting beat 2 fixes it.

## The anchor contract

Four of the five beats are not written per lead. They are drawn from Haytham's
hand-written lines, and the drafting model writes *against* them.

**The model may re-voice an anchor so the beats connect. It may not change what
the anchor claims.** That single sentence is the whole arrangement: it buys real
freedom for the drafter — the beats read as one email instead of five stapled
sentences — while keeping every claim traceable to a line a person wrote and
checked.

Both halves are enforced. Claim preservation is checked per email; whether the
drafter used the line it was actually dealt is checked on both the reported id
**and the written text**, because a drafter that quietly drew its own line ships
an email that reads perfectly and a CRM row naming a sentence the reader never
saw.

### A batch is dealt, not rolled

The lines are allocated across the whole batch at once, so the declared weights
actually hold. Per-lead hashing is unbiased only in the limit, and batches are
not that big: measured on the live lines, a 50-lead batch gave one offer line 8%
against a declared 20% and pushed another over the repetition cap. It converged
somewhere near n=200. Dealing gets the worst miss to about a point.

**The repetition cap outranks the exact-match ratio.** The draw prefers an
identity line matched to the lead's segment, but when a segment has too few
usable lines to spread its share, the excess spills to generic rather than
putting one sentence in front of most of a batch. Two coaches who compare notes
and find the same email is a worse outcome than one coach getting a slightly less
specific line.

The spill is the workaround, not the fix. The fix is more lines in that segment,
and the deal reports which segments are thin and by how many.

## Numbers

**Every number in an email must be true of a real client result**, and
`copy/results.csv` is the authority. That file is repo-only on purpose: the lines
are voice and get tweaked, the results are audited evidence and should not be
casually editable.

**A number next to a named segment must belong to that segment.** Widening to
"coaches here" is honest. Calling a Business result a health coach's is not.
These are two different failures — invention and relabelling — and both are the
tell that the whole email is fabricated, hook included. The client results are
real, they come up on the call, and these coaches compare emails.

### How "no price in any email" is actually held

Stated precisely, because a spec that claims a check it does not have is worse
than one that claims nothing.

**There is no price check.** The linter admits only numbers that resolve to the
lead's own fact set — that segment's row of `copy/results.csv`, plus the small
set of offer numbers the copy is allowed to use (ten names, fifteen minutes,
forty others, and their kin). A price is rejected as an *untraceable number*, not
as a price. There is no rule in the code with the word "price" in it.

The consequence worth knowing: the protection is a side effect of traceability.
Widen the allowed number set carelessly and the wall between the inbox and the
call gets thinner without anything appearing to change.

## The copy rules

Every one of these was a rule before it was code, and every one is now checked.

- **No em-dashes.** Ever.
- **No operator jargon.** Funnel, conversion, audit, sequence, pipeline,
  outreach, optimise. The reader is a coach, not an operator.
- **No weak closers.**
- **No bare domains or email addresses in the body.**
- **No gendered pronoun in an identity line.** The line goes to whoever draws it.
- **Numbers carry separators.**
- **Sign off "Haytham".**
- **Subject lines are not reused across a batch.**

The jargon check matches on word boundaries with explicit suffixes, and that
detail is load-bearing: a raw substring test rejected whole emails because the
lead's own quoted words contained "optimism", "auditorium" or "Detroit". A gate
that rejects a good email and names a word that was never in it is unfixable by
the drafter, because the complaint is not true.

## Batch-level checks

Some failures are invisible one email at a time. Three of the five beats come
from a pool of a dozen sentences, so two coaches who compare notes can see the
same offer, close and ps word for word. Share caps run across the whole upload
file, and only above a minimum batch size — below it, a "share" of four emails is
noise and the caps report as warnings instead.

## The gate no check replaces

**Read `out/preview.txt` before uploading. Ten emails, in full.**

The linter catches invented numbers, relabelled numbers, lost claims, jargon,
bare links and repetition. It cannot catch a hook that lands wrong on a specific
person, or a paragraph that passes every rule and still reads like a robot. That
has always been the gate and it still is.

## What is unknown

- **None of these rules has been tested against reply rate.** They are reasoned
  from one campaign's post-mortem and a lot of cold reads. Hook type is recorded
  per lead precisely so it can become a variable rather than a belief.
- **The word budget is inherited, not measured.** 67 to 95 is where the good
  drafts landed, not a number anyone A/B tested.
