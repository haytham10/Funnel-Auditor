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

**Nothing downstream consumes `work/identity.json` yet.** Do not hand it to the
research workers and do not let a verdict in it change what they are told. It is
here to be read and measured for a batch before anything is built on it, which
is the same way the ledger and the observation contract arrived.

## Stage 1c — what it would cost to look

```
python main.py plan work/identity.json --leads work/clear.json --out work/plan.json
```

Free, and it fetches nothing at all — it describes a ladder, it does not walk
one. Quote the `PLAN:` line. The number that matters is **would decline**: how
many paid rungs point at a channel that names somebody else. Pair it with the
`NO RUNG` lines, which are the leads where free retrieval found nowhere to look
— on the first batch three leads walked the whole ladder and returned nothing,
and that cost three full agent passes to discover.

**It declines nothing, and you must not either.** There is no flag on this run
that would. Every rung it labels `decline` is still in the file, because nobody
yet knows whether the leads with no confirmed channel are the leads that produce
no hook — and that is exactly what this batch is being run to find out. If they
are the same leads, declining is free. If they are not, `plan` should not gate
on ownership at all, and it is much better to learn that before it is built.

**Nothing consumes `work/plan.json` yet.** Do not hand it to the hook workers
and do not let a `decline` change which rung anybody walks. `hook-worker` keeps
its own ladder this batch, on purpose.

## Stage 2 — research

Fan out `research-worker`, one per slice of ~10 leads, at most 5 at a time.
Give each worker its slice, the relevant part of `work/sites.json`, and the
Apify budget note.

Workers **write nothing**. They return typed research objects. Validate each:

```
python main.py research work/research-<slice>.json
```

That checks the observations each object carries too — one record per page or
post the worker actually read, text verbatim. To see only those, or to hand a
worker back a shorter list to fix:

```
python main.py observe work/research-<slice>.json
```

**Nothing consumes observations yet.** They do not change what gets drafted, and
stage 3 still does its own fetching. They are the evidence this pipeline used to
throw away — a post read once, reduced to a boolean, and paid for again one
stage later.

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

## Stage 3 — hooks

For every lead that passed the floors and has a verified address, fan out
`hook-worker`, then `hook-verifier` on each proposal. The verifier never sees
the worker's search — that independence is the entire mechanism, so do not
summarise the worker's reasoning into the verifier's prompt.

Pipeline these: a hook can be verified while other hooks are still being found.
Do not wait for all the workers before starting any verifier.

A REFUTED or INCONCLUSIVE hook means that lead is not drafted this round. Say so
in the brief. Do not substitute a weaker hook to keep the count up.

**Quality tripwire:** if the verifier refutes 2 or more of the first wave, stop
and show Haytham before spending the rest of the queue. Something is wrong with
the instructions, not with those two leads.

**The verified hook's date is the activity evidence — write it back.** The
active-in-30-days floor runs at stage 2 against a site read, and a coach's own
website almost never carries a date: measured across nine real sites and about
220,000 characters, zero usable ones, so every lead came back `unclear` and the
floor did nothing. LinkedIn is where the signal is, and this stage is what
fetches it. When a hook is VERIFIED with a real date, put that date on the lead
as `last_activity` before stage 4, so the CRM records when they were last seen
rather than a shrug. A hook dated outside the window is not a kill — the lead is
already through the floor — but it is worth a line in the brief, because a coach
whose newest public thing is five months old is a different prospect from one
who posted yesterday.

## Stage 3b — would a ranker have found it without fetching

Once every hook has been verified or refuted, and the hook fields are written
back onto the research objects:

```
python main.py select work/draftable.json --against --out work/select.json
```

No fetching, no model, no clause. It ranks the observations the research workers
already returned and reports how its choice relates to the hook the stage
actually verified. Quote the `AGAINST:` line, and read the `MISSED` and
`UNOBSERVED` lines under it rather than the totals.

Those two words are the whole point and they mean opposite things:

- **MISSED** — the hook's page *was* observed and the ranker passed it over. It
  names the ban that dropped it. A wrong ban is a three-line fix.
- **UNOBSERVED** — the hook cited a page no observation carries. That is the
  fetch selection could not have replaced, and it is the number that decides
  whether the hook stage can stop fetching at all.

**Nothing consumes `work/select.json`.** It never replaces a verified hook, it
does not change which lead is drafted, and a disagreement is not an error — it
exits 0 whatever it finds, the same way the ledger reports a duplicate without
failing on it.

**And it verifies nothing.** A quote it found is in the text we stored, not on
the page. The verifier's live re-fetch is the only thing that has ever caught a
fabricated claim, and reading this output as verification is how that gets
quietly retired.

## Stage 4 — draft

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

Then, for every lead with a VERIFIED hook at once, deal the anchors:

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

Then fan out `draft-worker` with the hook, the research object and **that lead's
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
made for the larger batch. Dropping 3 of 11 on the first real run put two ps
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

Copy `work/select.json` to `data/runs/<batch>-select.json` and commit that too.
It is the other half of the same baseline — what the retrieval cost, and whether
a ranker over what was already retrieved would have reached the same hook.
`work/` does not survive the container.

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

## The brief

One message at the end. Never a per-lead narration.

```
BATCH <date>: <n> written of <m> raw
  intake     <n> live site, <n> social only, <n> nothing to work
  dedupe     <n> already contacted (<n> WARM), <n> internal duplicates
  tier 0     <n>% of sites read free, <n> escalated
  floors     <n> passed, <n> failed (<which floors>)
  address    <n> verified, <n> enriched, <n> none
  hooks      <n> verified, <n> refuted, <n> not found
  plan       <n> rung(s), <n> WOULD-decline on ownership, <n> lead(s) no rung
  select     <n> agreed, <n> shortlisted, <n> missed, <n> unobserved, <n> no pool
  drafts     <n> send, <n> rewritten, <n> rejected
  lines      top line <n>% of the batch (cap 35), <n> THIN segment(s)
  copy       live from Airtable | cached (say which, always)
  cost       $<x> Apify this run, $<x>/lead (quote `ledger report`)
  retrieval  <n> fetch(es), <n> duplicate, <n> blocked by the cost gate
  → out/leads.csv   READ out/preview.txt BEFORE UPLOADING
  then       wall-add + copy-usage, once it is actually uploaded
```

Then say plainly: **read the preview before uploading.** There is no automated
gate that replaces it. The linter catches invented numbers and lost claims; it
cannot catch a hook that lands wrong on a specific person. Read ten in full.

## The rules that do not bend

- **Never send an email.** The machine ends at a file.
- **Never log in as Haytham anywhere.** Read-only, no-login tools only.
- **Never invent a hook or a number.** No evidence means the null answer.
- **Cross-check the store, not the worker's word.** For every consequential
  result, re-read the record and confirm the write landed. A claimed success
  over an unwritten row is Blocked, not Done.
- **Size the batch to what Haytham can actually send.** A thousand-row upload
  file against thirty sends a day is nine hundred stale rows.
