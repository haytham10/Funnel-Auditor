# 2026-08-02-q3 — batch state, snapshotted because `work/` and `out/` are gitignored

The container is ephemeral and both directories are in `.gitignore`, so without
this the whole batch would be gone: 34 researched leads, 17 verified hooks, and
the emails that passed a cold read. Committed mid-run because a session limit
stopped the redraft with work outstanding.

## Where the batch actually is

**Shipped, 5.** `leads.csv` here is the same file as `out/leads.csv`, complete
and uploadable: Sam Eid, Anas Mounir, Stefania Brunori, Leila Atbi, Lisa Zevi.
All five passed lint, `export --anchors`, and an independent cold read.
`preview.txt` is the gate and should be read before any upload.

**Held with a verified hook, 11.** Every one has a certified hook, a dealt set
of four lines and a research object. Only the drafting failed. Nothing needs
re-fetching to finish them.

**Withdrawn, 1.** Amjad Saijary, by his own drafter: the post his hook cites
says he open-sourced the project "not to sell it", so no honest bridge to a
prospecting offer exists. Do not re-attempt without new evidence of something
he sells and to whom.

## What was in flight when the limit hit

All 17 drafts failed their first cold read, on two failures that repeat almost
word for word. `.claude/agents/draft-worker.md` was corrected for both (commit
a5ddf4d) and the 11 held leads were relaunched against the corrected file.

Two landed and are in this directory, both linting PASS and **neither yet cold
read**:

- `draft-govind-abkari.json` — figures split across three sentences instead of
  stacked, "practices" replaced with "coaches", "pitch" gone from the clause.
- `draft-stephan-melchior.json` — the clause now points at a decision only he
  made (he published the diagnostic free) rather than at diagnostics generally.

Nine did not run: David Singleton, Dalia Hosny, Solene Anglaret, Anita
O'Connor-Roberts, Sarah Zakzouk, Amanda Slade, Meg Juma, Bahar Selman, Chris
De Nil. Their files here are the **held** versions, not redrafts.

## To resume

1. Cold read the two redrafts above. They have had no verifier.
2. Redraft the nine, then cold read them.
3. Rebuild `work/drafts.json` from every draft that reaches SEND, re-run
   `export --anchors work/anchors.json --rebalance-ps`, then `crm-rows` and
   `metrics`. The per-lead findings each of the nine has to answer are in
   `docs/journal.md` and in the session that produced them.

`anchors.json` is the deal this batch was written against. **Do not re-deal.**
The drafts and CRM rows are written against it, and a second allocation makes
them disagree — which is what `export --anchors` exists to catch.

## Not done

`wall-add` and `copy-usage` have NOT been run, because nothing has been
uploaded. Run them only after the upload actually happens: walling a lead who
received nothing silently excludes them from every future batch, and
`copy-usage` is additive rather than idempotent.
