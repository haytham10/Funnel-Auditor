---
name: outbound-batch
description: Run a raw list of coaches end to end into a Smartlead upload file. Use WHENEVER Haytham drops a CSV of leads, says "run this list", "build a batch", "process these leads", "make me an upload file", or names a lead file. It profiles and dedupes the list before spending anything, researches the survivors, finds and independently verifies a hook per lead, drafts each email against the hand-written anchor lines, lints every draft, and writes leads.csv plus preview.txt. It never sends anything — sending is Smartlead's job, and the upload is Haytham's.
---

# Run a list end to end

The whole machine in one skill. You are the orchestrator: you fetch, you fan
out, you cross-check, and you write the file. You do not do per-lead work
yourself unless a worker stalls.

**The machine ends at a file.** No email leaves from here. Do not offer to send
one.

## Before anything is spent

Name the batch first. It is one command and it is the cheapest thing here:

```
python main.py ledger batch <YYYY-MM-DD[-qN]>
```

That writes `work/BATCH`, and every later command and **every subagent** reads
the label from there. On `2026-08-01-q1` the label was passed by telling twelve
workers to add a flag that did not exist — `OUTBOUND_BATCH` is a shell variable
and a subagent is a different process, so it inherits nothing. Fifteen
retrievals, five of them paid hook rungs, landed in a file named after the date
instead of the batch, and `ledger report` under-reported the run by 30%. Nobody
has to be told the label now. Do not tell them.

Run `python main.py ledger batch` with no argument at any point to see which
label resolves and where it came from.

```
python main.py intake <list.csv> --out work/leads.json
```

Read the profile out loud to Haytham. If more than about half the rows have no
research target at all, say so before continuing — that is a list quality
problem and no amount of research fixes it.

Then the wall, which runs **before any paid call**:

```
python main.py dedupe work/leads.json --out work/clear.json
```

The wall is `data/contacted-before.csv`, in the repo. No fetch, no argument —
it is read on every run and it is the cheapest check in the machine. An
unreadable wall exits 2 rather than passing the batch, because a missing file
must never read as "nobody has been contacted".

**A warm hit exits 1 and stops the run.** Show Haytham the names. A cold opener
landing on a live conversation is the one failure here that destroys something
rather than wasting something, and it has already happened twice.

Finally, check the Apify budget **once for the whole batch**, not once per
worker:

```
python main.py apify limits
```

Pass the answer into every worker prompt. If it is near cap, tell the workers to
prefer `unclear` over a paid call.

## Stage 1 — the free site read

```
python main.py fetch work/clear.json --out work/sites.json --with-text
```

This is tier 0: local HTTP, no cost. It prints what share of sites it read for
free and a plan for the rest. **Report that share to Haytham** — nobody has
published a real number for this niche and it is the single most useful thing
this run can measure.

If it emits an escalation plan, that is ONE batched Apify run for every failed
URL, not one per lead. Run it that way or not at all; fifty separate two-page
runs is the worst possible way to use a compute-billed actor.

**If the escalation fails, retry with `--escalate-only`, never by re-running
`fetch --escalate`:**

```
python main.py fetch work/sites.json --escalate-only --approve-cost
```

`--escalate` reads every site at tier 0 *before* it escalates, so a retry reads
them all a second time. On `2026-08-01-q1` one retry after a 403 put **52
duplicate `(lead, url)` pairs** into the ledger of the batch whose entire
purpose was to produce a duplicate count — 52 of the 83 recorded, and only 12
of the total were real findings. D22 names that risk in advance and it happened
anyway, because avoiding it meant calling into the module by hand. Now it does
not.

## Stage 1b — whose channels are these

```
python main.py resolve work/clear.json --sites work/sites.json --out work/identity.json
```

Free, and the only thing it fetches is the link-in-bio page — a linktree lists
every channel a coach has and no stage has ever read one. Quote the `RESOLVE:`
line. The number that matters is how many leads have **no confirmed channel**:
about 40 of 151 rows on the first batch pointed at somebody else entirely, and
every one was found by a worker, by hand, after the fetch had been paid for.

**It drops nobody, and you must not either.** A channel that names somebody else
is a thing not to spend on. It is never a reason to skip a lead, and there is no
exit code here that says otherwise — a false kill is permanent and invisible.

**`plan` consumes this now, and a decline binds** (D27), so an ownership verdict
here has consequences it did not have for the first two batches. That makes the
`no confirmed channel` count worth reading rather than noting.

**Still do not hand it to the research workers**, and do not let a verdict in it
change what they are told. It gates a *purchase* at stage 1c and nothing else. A
channel that names somebody else is a thing not to spend on; it has never been
and is not now a reason to research a lead less thoroughly.

## Stage 1c — what it would cost to look

```
python main.py plan work/identity.json --leads work/clear.json --out work/plan.json
```

Free, and it fetches nothing at all — it describes a ladder, it does not walk
one. Quote the `PLAN:` line. The number that matters is **declined**: how many
paid rungs point at a channel that names somebody else. Pair it with the
`NO RUNG` lines, which are the leads where free retrieval found nowhere to look
— on the first batch three leads walked the whole ladder and returned nothing,
and that cost three full agent passes to discover.

**The declines bind now** (D27). A `hook-worker` may not escalate onto a rung
labelled `decline`, so this file is what stops a paid scrape of somebody else's
LinkedIn. Hand each hook worker its lead's `LeadPlan` at stage 3b.

**A decline gates spend and never inclusion.** A lead whose every paid rung is
declined still gets researched, still gets a plan, and still gets a row — it
just gets a null hook instead of a purchase, and a null hook is a good answer.
Nothing here drops anybody and you must not either.

**Run `metrics --plan work/plan.json` after the batch.** Of the leads carrying a
decline, how many produced a verified hook is D21's reversal condition, and it
is the whole reason this gate was held back for two batches. A run of the gate
without its measurement is the thing `plan` spent those batches refusing to be.

## Stage 2 — research

Fan out `research-worker`, one per slice of ~10 leads, at most 5 at a time.
Give each worker its slice, the relevant part of `work/sites.json`, and the
Apify budget note.

Workers **write nothing**. They return typed research objects. Validate each:

```
python main.py research work/research-<slice>.json
```

That checks the observations each object carries too — one record per page or
post the worker actually read, text verbatim. **`research` is the gate; the
command below is the magnifying glass.** To see the observations alone, or to
hand a worker back a shorter list to fix:

```
python main.py observe work/research-<slice>.json
```

It unwraps the research objects and validates what is nested inside them,
reporting how many it found over how many leads. Until the 2026-08-01 batch it
did not unwrap, so it graded ten perfectly good research objects *as*
observations and printed fifty violations about missing platforms and urls that
were never missing. If you ever see that shape again, read the count line
first: `unwrapped <n> observation(s) from <n> research object(s)` is what a
research file should produce.

**These observations are the whole of what the hook stage will have.** `qualify`
settles `active_recent` from the newest date, and as of D27 `select` ranks them
and `hook-worker` quotes them — it does not fetch. So **an observation a worker
does not return is a hook nobody can find**, and it will look like the lead's
fault rather than the retrieval's.

That is the one thing worth pushing back on a thin slice about. A worker that
settled every floor correctly and returned two observations has done half its
job now. Read the count line: `unwrapped <n> observation(s) from <n> research
object(s)` — a slice of ten leads returning ten observations is a slice that
answered floors and kept nothing quotable.

A schema violation goes back to the worker once. A worker that returns a
status-only reply with no work product gets taken over directly, not resumed
twice.

**A missing output file is not proof a worker is dead.** Confirm it before
relaunching. On the first batch slice 15 finished with no notification and no
file, was relaunched on that inference, and then the original returned too — so
the slice ran twice for one result, at double the cost and with two objects to
reconcile. Check whether the agent is still running first; a slow slice and a
dead one look identical from the file system.

Then the late dedupe, now that addresses exist:

```
python main.py dedupe work/researched.json --stage late
```

Write the survivors to `work/draftable.json` — every lead that passed the floors
and has a verified address. That is the set the next three stages work on.

## Stage 2b — the lines, before the hook is written

**Deal here, not after the hook.** The bank leaves between 12 and 36 words for a
hook depending on the draw, and dealing afterwards meant a hook could be found,
verified against a verbatim quote, and then handed to a drafter with 12 words of
room — so the drafter compressed a sentence an independent verifier had just
certified. The four lines are never available to it to cut instead. Knowing the
room first is what makes that impossible rather than merely discouraged.

**Airtable's Copy Assets table owns every line.** `copy/*.csv` is a cache of it,
not a second opinion. Check that first:

```
python main.py copy-check
```

Quote its line. `PASS` means the live table is what this batch will draw from
and the cache matches it. `FAIL` names either a live line that fails the linter
— fix it in Airtable, nothing here can — or a cache that drifted, fixed with
`python main.py copy-sync --live` and a commit of `copy/*.csv`. `BLOCKED`
(exit 2) means there is no key or no network, so the check could not look.

Then deal the whole draftable set at once:

```
python main.py deal work/draftable.json --out work/anchors.json
```

`deal` re-enforces the same thing rather than trusting you ran the check. It
prints a `COPY:` line naming where the lines came from, exits 1 if the live
table answered with lines that fail the linter, and exits 1 if the table could
not be read at all unless you pass `--allow-cached-copy`. Use that flag only
when Airtable is genuinely unreachable and the batch has to go out anyway; it
means anything edited since the cache was written is not in these emails.
**Say which happened in the brief either way.** The bank is cached once per
process, so a big batch makes one request rather than one per lead.

**Deal, do not loop `anchors`.** That command is the single-lead path for
`outbound-draft`. Per-lead hashing is unbiased only in the limit: at 50 leads it
missed a declared 20% weight by 12 points and broke the repetition cap. Dealing
the batch hits the weights as closely as whole leads allow.

Read the `THIN` lines it prints. They name a segment with too few identity lines
to hold its share without repeating a sentence, and the fix is writing one more
line for that segment in Airtable, not anything in code.

**The cost of dealing here: lines get allocated to leads that later hold.** A
refuted hook means that lead's four lines went unused, so the shipped batch
drifts from the declared weights. That is what `export --rebalance-ps` exists
for and the skill already tells you to pass it whenever any lead held — it will
now fire on most batches rather than some. Quote the drift it reports in the
brief. Do not re-run `deal` after the hooks to tidy it up: the drafts and the
CRM rows are written against this file, and a second allocation makes them
disagree.

Note the `hook room <lo> to <hi> words` line. The room is **per lead** — it
depends on how long that lead's four lines came out — and each lead's own number
is the `hook_room` field on its entry in `work/anchors.json`. Stage 3 hands each
hook-worker its lead's number. Stage 3b takes one number for the batch, and the
low end is the one to pass: its check is a warning about a pick that will not
fit, so the tighter figure is the honest input.

## Stage 3a — rank what research already retrieved

```
python main.py select work/draftable.json --hook-room <n> \
  --batch <YYYY-MM-DD> --out work/select.json
```

`<n>` is the **low** end of the hook-room range `deal` printed at stage 2b.

**This runs before the hooks now, and the hook stage reads it** (D27). It ranks
every observation the research workers returned and hands each lead up to three
candidates carrying the observation's stored text. No fetching, no model, no
clause.

Quote the `SELECT:` line. The number that matters is **how many leads have a
candidate**: a lead with none will produce a null hook or an escalation, and
knowing which leads those are before you spend an agent pass on them is most of
what this stage buys.

**`--batch` writes the corpus as well as the verdict**, into `data/runs/`.
Commit both. On `2026-08-01-q1` only the verdict was kept and the corpus lived
in `work/`, which does not survive the container — so when the ban that caused
all three MISSED turned out to be wrong, the batch that proved it could not be
re-scored.

**It verifies nothing, and that matters more now than it used to.** A quote in
this file is in the text *we stored*, written down by a research worker at a
different hour. Whether those words are on the page is the verifier's live
re-fetch at stage 3b, and it is the only thing that has ever caught a fabricated
claim.

## Stage 3b — write the hook, gate it, verify it

For every lead that passed the floors and has a verified address, fan out
`hook-worker`, then `hook-verifier` on each proposal.

**Give each worker three things**: its lead's entry in `work/select.json`, the
`hook_room` on its entry in `work/anchors.json`, and its `LeadPlan` from
`work/plan.json`. The plan is what tells it which rung an escalation may use and
which are declined.

The verifier gets none of them and must not. Its question is whether the words
are on the page; a length note is a reason to be lenient about a quote that
nearly fits, and the worker's reasoning is the thing it is supposed to be blind
to. **Do not summarise the worker's choice into the verifier's prompt.**

**Each worker runs the gate on its own proposal before returning:**

```
python main.py hook work/hook-<lead>.json --against work/select.json
```

`--against` is what checks the quote really is a contiguous piece of the
observation it names — ban #3, mechanical for the first time, because until the
hook stage read a shortlist there was nothing to check a quote against. A worker
that reports a hook with no PASS line has skipped it.

Pipeline these: a hook can be verified while other hooks are still being found.
Do not wait for all the workers before starting any verifier.

A REFUTED or INCONCLUSIVE hook means that lead is not drafted this round. Say so
in the brief. Do not substitute a weaker hook to keep the count up.

**Two tripwires, and they mean different things.**

- **Refutes.** If the verifier refutes 2 or more of the first wave, stop and
  show Haytham before spending the rest of the queue. Post-flip this is the
  sharper signal it used to be: a refuted quote now means the *stored text* did
  not match the page, so two of them is a research-stage problem reaching the
  reader, not two hard leads.
- **Escalations.** If more than about a third of the first wave escalates, stop.
  That is the flip failing rather than those leads being difficult, and the fix
  is research fetching deeper — not more escalations. Quote the count.

**A null hook is cheaper than an escalation and is a good answer.** Make sure
the workers know you mean it; an orchestrator that reacts to null hooks by
pushing for more escalation converts the honest outcome into the expensive one.

**Write the verified hook's date back, for the CRM.** When a hook is VERIFIED
with a real date newer than the lead's `last_activity`, put it on the lead
before stage 4, so the row records when they were last seen. A hook dated
outside the window is not a kill — the lead is already through the floor — but
it is worth a line in the brief, because a coach whose newest public thing is
five months old is a different prospect from one who posted yesterday.

**Write `observation_id` back too.** It is what `metrics` counts escalations
from: a hook with no `observation_id` is one the shortlist did not hold.

## Stage 4 — draft

The lines were dealt at stage 2b. Read `work/anchors.json`; do not deal again.

Fan out `draft-worker` with the hook, the research object and **that lead's
four dealt lines, inline in the prompt**. The worker must not draw its own: it
would get the single-lead line rather than the dealt one, which breaks the
balancing you just paid for and leaves the CRM record disagreeing with the email
that shipped.

Each draft goes to `draft-verifier`, which reads it cold.

- **SEND** → into the export set.
- **REWRITE** → back to the drafter once, with the verifier's note. Then it
  either passes or it holds.
- **REJECT** → holds. No row.

## Stage 5 — the file

```
python main.py export work/drafts.json --anchors work/anchors.json \
  --out out/ --batch <YYYY-MM-DD>
```

**Export against the SAME deal file the drafts were written from.** Re-running
`deal` after drafting produces a different allocation — copy edits, a changed
pool, a different lead set all move it — and `--anchors` then compares each
draft against lines it was never given. The rejection reads "the drafter drew
its own instead of using the batch's", which is the opposite of what happened
and sends you looking at the wrong stage. Keep `work/anchors.json` for the life
of the batch, and if you must re-deal, re-draft.

**Pass `--rebalance-ps` whenever any lead held.** Holds are guaranteed — a
refuted hook, a twice-refused draft — and every hold unbalances a deal that was
made for the larger batch. **Since the deal moved to stage 2b this is most
batches, not some**: refuted hooks now land after the allocation rather than
before it, which is the price of the drafter knowing its hook room in advance.
Dropping 3 of 11 on the first real run put two ps
lines at 38% against a 35% cap and the batch check blocked the whole file,
correctly. Re-dealing from scratch is the wrong answer: it moves identity lines
too, which means re-drafting emails that already passed a cold read. The ps is
the one beat that can move safely — library copy, reproduced near-verbatim, sat
alone at the end, no part in the seam — so this is an allocation decision, not a
drafting one. It respects the word ceiling and the echo rule as well as the cap,
and reports how many lines it moved.

**Pass `--anchors`.** It rejects any draft whose lines disagree with what the
deal assigned, which is the mechanical version of the instruction above. Two
checks, because the line id is self-reported: the id against the deal, and the
written text against every other line in that beat. Re-voicing the assigned line
is fine and expected; reproducing a *different* line verbatim while reporting
the assigned id is not, and it produces an email that reads fine alongside usage
counts and a CRM row describing an email nobody received.

It writes only what passed, blocks the whole file on a batch-level failure, and
lists every rejection with its reason. Five files come out:

- **`leads.csv`** — exactly eight columns for Smartlead: `email`, `first_name`,
  `last_name`, `website`, `linkedin_profile`, `location`, `subject`, `body`. Nothing
  analytical; that belongs in Airtable.
- **`preview.txt`** — the gate. Read it.
- **`rejected.txt`** — every lead that did not make the file, with its reasons.
- **`wall-additions.csv`** and **`line-usage.csv`** — both held back
  deliberately. See below.

Then write the batch to Airtable: one **Batches** row, and one **Leads** row per
lead including the ones that held, with their Blockers. A lead that vanished
with no record is worse than a kill you can read.

**Build the Leads rows, do not assemble them:**

```
python main.py crm-rows work/clear.json --research work/researched.json \
  --drafts work/drafts.json --batch <YYYY-MM-DD> --out out/crm-leads.json
```

Then write `out/crm-leads.json` through the MCP. **Nothing in the repo touches
the CRM** — the boundary is that a Lead row lands where a human sees it, and
this command computes rather than writes.

On `2026-08-01-q1` the rows were assembled by hand from `work/researched.json`
alone, and twenty of them landed with **no First Name, Last Name, Website,
LinkedIn or City**. Those fields live on the normalized Lead and never have been
on a research object; a filter dropped every empty key before the request, so
there was no error. `crm-rows` fails closed on that exact join.

**Read its coverage block, not just its PASS line.** The check that passed those
rows counted Name, Status, Hook Verified and Blockers, saw 20/20, and called it
cross-checked — four fields somebody expected to be populated. The block prints
every field, and a `0/n` is worth one look at the source list before you decide
it is fine. `Instagram 0/20` was correct on that batch. `First Name 0/20` was
the bug.

`Batch` is a linked field and is not in the rows; link each to the Batches
record after you create it.

**Do not compute the Batches numbers yourself.** Run `metrics` (below) and paste
its `BATCHES ROW` block, field for field. Python does not write this row — the
boundary in `audit/airtable.py` is that a row lands where a human sees it, and
that stays. What was wrong was never that a model did the typing; it was that a
model did the *arithmetic*, from memory, at the end of a long run. Every value in
that block is measured or `?`.

**A `?` is not a zero and must not be typed as one.** Leave the cell empty. A
`0` in `Apify Cost USD` from a batch nobody costed is a wrong number that stays
in the CRM and gets believed for months.

## Stage 6 — after Haytham uploads

```
python main.py wall-add out/wall-additions.csv
```

```
python main.py copy-usage out/line-usage.csv
```

**Both only after the upload has actually happened.** Nothing was sent at export
time, and walling a lead who never received anything would silently exclude them
from every future batch.

`wall-add` is idempotent. `copy-usage` is **not** — it adds to a running total,
and nothing can tell a re-run from a genuine second batch using the same lines.
Run it once, `--dry-run` first if unsure.

Then commit `data/contacted-before.csv`. That commit is the wall's history.

Commit `data/runs/<batch>.jsonl` in the same breath. That is what the batch
cost, and it is the baseline the next one gets compared against.

Commit `data/runs/<batch>-select.json` and `data/runs/<batch>-research.json`,
which stage 3b's `--batch` already wrote. They are the other half of the same
baseline — what the retrieval cost, whether a ranker over what was already
retrieved would have reached the same hook, and the corpus that answer was
computed from. **`work/` does not survive the container**, so anything left
there is gone by the next session.

### Later, when replies exist

Not part of the run. Whenever Haytham exports a replies CSV from Smartlead:

```
python main.py replies <smartlead-export.csv> --leads work/draftable.json \
  --batch <YYYY-MM-DD>
```

This is the only path this repo has to reply data — Smartlead owns replies and
there is no API key here — and it is what makes `hook_type` testable against
reply rate, which is the reason `Hook Type` is a select in the CRM at all. Its
own field description calls it *"a testable variable against reply rate rather
than a detail buried in prose"*. The variable has existed since the beginning
and the test has never been run.

It sniffs the export's columns. If it cannot identify one it **exits 2 naming
the headers it saw** rather than reporting a zero reply rate, because a zero
would read as "the campaign did nothing" when the truth is "the question could
not be asked". Pass `--email-column` / `--replied-column` to name them, or
`--all-replied` if the export is already filtered to people who replied. **Never
pass `--all-replied` to make an error go away** — a pre-filtered file and an
unrecognised column look identical and differ by the whole answer.

Read its `NOT A VERDICT` line and mean it. One batch is a handful of samples per
bucket, and the difference between 1 of 1 and 0 of 1 is noise wearing a
percentage. Commit `data/runs/<batch>-replies.json`; the point is that it
accumulates.

## What the run cost

Read this before writing the brief, and quote its first line into the `cost`
row rather than adding up Apify calls by hand:

```
python main.py ledger report --leads <the batch's lead count>
```

Pass `--leads` — without it, cost per lead is computed over only the leads that
needed a fetch, which reports several times the real figure on a batch where
most leads were settled free.

Two lines in that output are worth reading rather than skimming:

- **`DUPLICATE`** — a page fetched twice for one lead, for something other than
  verification. The known one is `li-posts`, run once by `research-worker` and
  again by `hook-worker` on the same profile, and it is the most expensive call
  in the machine on the one actor that cannot be batched. It is expected today;
  it is what the retrieve-once work is being measured against. Note the count in
  the journal.

  **This is one half of a pair.** `DUPLICATE` says what the second fetch cost;
  stage 3b's `AGAINST:` line says whether it bought anything the first fetch had
  not already. Record both in the same journal entry or neither is decidable.
- **`BLOCKED`** — what the cost gate refused. A batch that quietly stopped at
  the threshold looks identical, in every other record kept here, to a batch
  that found nothing.

**The ledger never fails a run.** It reports; it does not block. And a missing
ledger exits 2 rather than printing a zero, so "no ledger" can never be read as
"this batch was free".

Every free WebSearch and WebFetch a worker ran is invisible to Python. A worker
records its own with `python main.py ledger add`, and those lines carry
`websearch` or `webfetch` so a reader can tell what was measured from what was
reported.

## What the run yielded

The ledger covers what Python can see. Everything on the hook side happens
inside an agent, so it used to be narrated into the brief from memory and lost
when the session ended — which is why every cost claim in the proposal had to be
reconstructed from a hand-written journal entry. Run this instead:

```
python main.py metrics work/draftable.json --batch <YYYY-MM-DD> \
  --plan work/plan.json \
  --raw <n> --after-dedupe <n> --warm <n> --passed-floors <n> \
  --written <n> --rejected <n> --tier0-rate <0.59> \
  --source-list <the raw list's name> --passes <n>
```

**`--plan` is not optional on a batch that ran the declines**, which is every
batch now. It reports how many leads with a declined rung produced no verified
hook, which is D21's reversal condition and the evidence the gate was held back
two batches waiting for. Without it that line prints `?` and the gate ran with
nobody collecting the number that judges it.

Every flag is a number an earlier stage already printed. **Pass the ones you
have and leave out the ones you do not** — an unsupplied count prints `?`, never
`0`, because a zero is a measurement and `?` is the honest word for a thing
nobody measured. Do not fill one in from memory to make the block look complete;
that is the exact habit this command exists to end.

`--passes` is the count of agent passes for the batch. Python cannot see it, so
it is **reported on trust** and printed as such, the same way `ledger add`
records a model-side fetch. **Prefer `ledger pass` over typing it**: record each
fan-out as it happens and the total derives itself.

```
python main.py ledger pass --stage draft --agent draft-worker --model opus --count <n>
```

One line per fan-out, `--count` for the size of it. `metrics` then prints
`passes_by_stage` and `passes_by_model`, which is what makes the Claude bill
readable at all — `2026-08-01-q1` cost about 64 passes for 20 leads and 5
shipped rows, and the only record was the number 64.

Quote the `METRICS` block into the brief. Four lines matter most, and the first
two are the ones this batch exists to produce:

- **`escalation_rate`** — hooks the shortlist did not hold. **This is D27's
  number**, and it is what says whether the flip holds. Rising means selection
  is not reaching the material and the fix is research fetching deeper, not a
  change to the ranker.
- **`declined_and_dry`** — of the leads with a declined rung, how many produced
  no verified hook. **This is D21's reversal condition**, and it is why the
  decline gate could finally be turned on.
- **`refute_rate`** — it means something new now. A refuted quote used to mean a
  worker misread a page it had open; post-flip it means the *stored text* did
  not match the page. That is a research-stage problem reaching the reader, and
  it is worth naming as one in the brief rather than filing under hook quality.
- **`wasted_retrieval`** — paid fetches on leads that produced no verified hook.
  **This is the number the whole retrieve-once effort is trying to move**, so a
  run without it is not a judged batch.

`yield_by_rung` still answers F5 — which rung the verified hooks actually came
from — and is worth a line whenever a rung yields near zero.

It writes `data/runs/<batch>-metrics.json`. Commit that alongside the ledger.

**It never fails a batch.** Same rule as the ledger: reporting a bad number is
the job, and a gate that can halt a send file over an accounting line is a gate
people learn to route around.

## The brief

One message at the end. Never a per-lead narration.

```
BATCH <date>: <n> written of <m> raw
  intake     <n> live site, <n> social only, <n> nothing to work
  dedupe     <n> already contacted (<n> WARM), <n> internal duplicates
  tier 0     <n>% of sites read free, <n> escalated,
             <n> page(s) deferrable had homepage-first been on
  floors     <n> passed, <n> failed (<which floors>),
             <n> settled active_recent from an observation date
  address    <n> verified, <n> enriched, <n> none
  hooks      <n> verified, <n> refuted, <n> not found
  plan       <n> rung(s), <n> DECLINED on ownership, <n> lead(s) no rung
  select     <n> lead(s) with a candidate, <n> had a pool and nothing survived
  drafts     <n> send, <n> rewritten, <n> rejected
  lines      top line <n>% of the batch (cap 35), <n> THIN segment(s),
             <n> ps moved by --rebalance-ps after the holds
  copy       live from Airtable | cached (say which, always)
  cost       $<x> Apify this run, $<x>/lead (quote `ledger report`)
  retrieval  <n> fetch(es), <n> duplicate, <n> blocked by the cost gate
  yield      hook_yield <n>%, null <n>%, refuted <n>% (quote `metrics`)
  by rung    <rung> <n> verified, ... — the number that settles F5
  wasted     <n> paid fetch(es), $<x> on leads that produced no hook
  FLIP       escalation_rate <n>% (<n> hooks the shortlist did not hold)
             declined_and_dry <n> of <n> declined leads produced no hook
             passes by stage and by model (quote `metrics`)
  → out/leads.csv   READ out/preview.txt BEFORE UPLOADING
  then       wall-add + copy-usage, once it is actually uploaded
```

Then say plainly: **read the preview before uploading.** There is no automated
gate that replaces it. The linter catches invented numbers and lost claims; it
cannot catch a hook that lands wrong on a specific person. Read ten in full.

## Model tiers, and the passes that are not free

The agent files declare their own tier and it is not yours to raise:

| Agent | Tier | Why |
|---|---|---|
| `research-worker` | sonnet | retrieval and typed extraction |
| `hook-worker` | sonnet | retrieval, and the gate now catches what it used to get wrong |
| `hook-verifier` | sonnet | one page, one quote, one verdict |
| `draft-worker` | opus | voice is the product in this beat |
| `draft-verifier` | opus | it caught 11 of 12 identity beats the linter passed |

**Do not upgrade a fan-out's tier ad hoc**, and do not downgrade the cold read
to save money. It is the check that found the one failure no linter can see, and
optimising the verifier is the trade this repo refuses twice in writing.

**The cheapest pass is the one nothing has to run.** Every mechanical gate here
exists partly for that: `hook` catches before a verifier is spent, `check_batch`
sees a template no per-email reader can, `crm-rows` replaces a script and the
audit of it. When something can be checked mechanically, it must not cost an
agent pass.

**Your own context is the largest single cost in a run.** Work from files and
quoted gate lines, not inline payloads. The workers return typed objects and
every gate prints one quotable line — that is what those two designs are for.
Reading twelve research objects into the main loop to decide something a
command already answered is the most expensive way to be sure.

## The rules that do not bend

- **Never send an email.** The machine ends at a file.
- **Never log in as Haytham anywhere.** Read-only, no-login tools only.
- **Never invent a hook or a number.** No evidence means the null answer.
- **Cross-check the store, not the worker's word.** For every consequential
  result, re-read the record and confirm the write landed. A claimed success
  over an unwritten row is Blocked, not Done.
- **Size the batch to what Haytham can actually send.** A thousand-row upload
  file against thirty sends a day is nine hundred stale rows.
