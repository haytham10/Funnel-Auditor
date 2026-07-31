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
python main.py dedupe work/leads.json work/contacts.json --out work/clear.json
```

`work/contacts.json` comes from Airtable's Contacted-Before table. Pull it with
`mcp__Airtable__list_records_for_table` and write it to disk; do not pass rows
through a prompt.

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

## Stage 2 — research

Fan out `research-worker`, one per slice of ~10 leads, at most 5 at a time.
Give each worker its slice, the relevant part of `work/sites.json`, and the
Apify budget note.

Workers **write nothing**. They return typed research objects. Validate each:

```
python main.py research work/research-<slice>.json
```

A schema violation goes back to the worker once. A worker that returns a
status-only reply with no work product gets taken over directly, not resumed
twice.

Then the late dedupe, now that addresses exist:

```
python main.py dedupe work/researched.json work/contacts.json --stage late
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

## Stage 4 — draft

For each lead with a VERIFIED hook, draw its anchors:

```
python main.py anchors <email> --coach-type <T> --sells-to <S> --json
```

Then fan out `draft-worker` with the hook, the research object and the anchors.
Each draft goes to `draft-verifier`, which reads it cold.

- **SEND** → into the export set.
- **REWRITE** → back to the drafter once, with the verifier's note. Then it
  either passes or it holds.
- **REJECT** → holds. No row.

## Stage 5 — the file

```
python main.py export work/drafts.json --out out/ --batch <YYYY-MM-DD>
```

It writes only what passed, blocks the whole file on a batch-level failure, and
lists every rejection with its reason. Then write the batch to Airtable: one
**Batches** row, and one **Leads** row per lead including the ones that held,
with their blockers. A lead that vanished with no record is worse than a kill
you can read.

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
  drafts     <n> send, <n> rewritten, <n> rejected
  cost       $<x> Apify this run
  → out/leads.csv   READ out/preview.txt BEFORE UPLOADING
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
