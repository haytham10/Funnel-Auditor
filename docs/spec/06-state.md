# Who owns which value

_Written 2026-07-31. This is the file that makes the rest of the set durable. The
previous doc layer died of holding values it did not own, and it died one
reasonable copy-paste at a time._

**Owns:** the authority for every value in this operation, and the rule that a
spec doc names a row here rather than copying from it.
**Defers to:** `docs/spec/00-index.md` — the doc contract this table serves;
`docs/spec/03-offer.md` — the one authority in the table that is itself a doc.
**Allows:** none.

## The table

| Value | Authority | Written by | Read by |
|---|---|---|---|
| every price, the guarantee, the offer stack | `docs/spec/03-offer.md` | a decision, recorded in `docs/spec/07-decisions.md` | the call |
| the hand-written lines | Airtable *Copy Assets*. `copy/identity.csv`, `copy/offer.csv`, `copy/cta.csv`, `copy/ps.csv` are a cache of it, never a second opinion | `copy-sync`, which validates and refuses; asserted by `copy-check` | `outbound/anchors.py` |
| what an identity line CLAIMS | Airtable *Copy Assets*, the `Claim` column. Its grammar and vocabulary are code, in `outbound/anchors.py` | by hand, next to the line it belongs to; refused by `copy-sync` if it names something the fact table has not got | `outbound/anchors.py`, `outbound/lint.py` |
| the client-result numbers | `copy/results.csv` | by hand, from `docs/identity-intake-raw.txt` | `outbound/lint.py`, `facts` |
| who has already been contacted | `data/contacted-before.csv` | `wall-add`, after the upload | `dedupe` |
| where each lead is right now | Airtable *Leads* | the batch run | the skills |
| what shipped in a batch | Airtable *Batches* | the batch run | reporting |
| the three floors, as evaluated | `outbound/qualify.py` | code | `qualify` |
| the research contract | `outbound/research.py` | code | every worker |
| the Apify cost ceiling | `audit/apify.py` | code | every paid call |
| the CRM base and table ids | `CLAUDE.md` | by hand, rarely | `audit/airtable.py` |
| the CRM's select options | Airtable, in the field config | by hand, in the UI | `audit/airtable.py`, `outbound/research.py`, `outbound/copy_sync.py`, all three checked against it by `doc-check --live` |
| what happened, and why | `docs/journal.md` | at the end of a session | the SessionStart hook |
| the run's output | `out/` | `export` | a person, before uploading |
| API keys | the environment | never the repo | the modules that need them |

## The rule

**No spec doc copies a value from this table. It names the row.**

A doc that says *the Apify ceiling is $X* is wrong the moment the constant moves,
and — worse — it is wrong invisibly, because nothing reads a doc. A doc that says
*the ceiling lives in `audit/apify.py`* is correct forever and sends the reader
somewhere that cannot lie to them.

The exception is the row where the doc **is** the authority: `docs/spec/03-offer.md`
holds prices because a price is a decision, not a measurement, and there is
nowhere better for it to live. That is why it is the only spec file permitted to
carry one.

## Why the wall is a file in the repo

`data/contacted-before.csv` is the check with the worst failure mode in the whole
machine and the lowest cost. It sits in the repo rather than the CRM because it
is read on every single run, never needs a view or a filter, and a network hop is
a strange dependency for the cheapest and most consequential check here.

Appending is a commit, so the wall gets a full history for free — which matters
the first time someone asks when a lead was actually contacted.

## Why the results are repo-only and the lines are not

They look like the same kind of thing and they are not.

**The lines are voice.** They get tweaked, reworded and retired, often several in
a sitting, and Airtable is a much better place to do that than a CSV. `copy-sync`
is what makes it safe: it validates every line against the linter and writes
nothing if anything fails, so an edit in Airtable cannot break an email.

**The results are evidence.** They come from `docs/identity-intake-raw.txt`,
eight hand-filled intake forms, and they are the thing every number in every
email traces back to. They should not be casually editable, so they are not in a
tool that makes editing easy.

**And a blank cell in them is not a zero.** It means nobody measured that, and a
Claim naming it is refused rather than resolved to nothing. `first_client_days`
is blank on six of eight rows for exactly that reason: two lines said a client
signed in week 1 and the table had no column for it, so the column was added
where the answer is known and left empty where it is not.

**The `Claim` is the other half of the results.** A line's words are voice and
belong in Airtable; the row and columns it draws its figures from are a
statement about evidence, and they sit next to the line so the person editing
it can see both at once. It is refused at sync if it does not resolve, which is
what keeps the two halves from drifting apart.

## Why one row in the table needs a check and the rest do not

Every other authority above is in this repo, so the rule is enough: a reader who
follows the pointer arrives somewhere that cannot lie to them, and a change to
the value is a commit that shows up in a diff.

The CRM's select options are the exception. They are edited in a browser by a
person who is not thinking about this repo, they have no diff, and three modules
mirror them so that a bad value is caught before a write fails at the CRM step —
which happens *after* the email is already in the upload file. A mirror of a
schema nobody here owns is a value that goes stale silently, which is exactly the
failure the rest of this file is written to prevent, and pointing at the
authority does not fix it because the pointer cannot tell you it moved.

So that row gets the thing a rule cannot give it: `doc-check --live` fetches the
live field config and compares. It is the only check in this repo that leaves the
machine, and that is the reason it is worth the network call.

**And it runs where the key is.** CI has no `AIRTABLE_API_KEY`, so on the one
path that runs automatically it cannot look. A Claude Code session has one, and
a push from that session is what opens or updates the pull request — so
`.claude/hooks/schema_drift.py` binds the check to the push and blocks it on
drift. A check that only runs when somebody remembers is the thing this whole
layer exists to stop relying on.

## State that is deliberately ephemeral

`out/` and `work/` are gitignored. They hold a single run's artifacts, and the
container is ephemeral anyway.

This is why the upload file is not the record of what shipped. **The record is
the wall plus the journal**, written after the upload — because the file existing
proves a batch was built, not that it was sent.

## What is unknown

- **Airtable *Leads* and the wall can disagree.** Nothing reconciles them, and
  nothing has needed to yet. The first time a batch is half-uploaded, something
  will.
- **`copy/results.csv` is eight rows from one intake sitting.** Every identity
  line in every email rests on them. Nobody has re-verified them since.
