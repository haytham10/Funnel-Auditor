# The doc contract

_Written 2026-07-31. The previous project had a defining layer — docs/uae-track/,
five numbered files — and it rotted inside three weeks. This set exists because
that failure is diagnosable, and the diagnosis is a rule a script can enforce._

**Owns:** what a defining doc is, the four layers, the header block every spec
doc carries, and how a spec gets changed.
**Defers to:** `docs/spec/06-state.md` — the table of who owns which value;
`outbound/doc_check.py` — the enforcement of the rules on this page.
**Allows:** none.

## The one rule

> **A defining doc states a decision and its reason. It never holds a value that
> something else owns.**

Where a value lives in code, a CSV, or Airtable, the doc **names the authority
instead of copying it**. Daily change then lands on the authority, and the doc
does not move.

That is the whole thing. Everything below is either a consequence of it or a way
of making it hold when nobody is watching.

## Why, with the receipts

The old set is in git at commit `89bf58b^`. It is worth knowing exactly how each
file died, because the failures were not sloppiness — every one of them was a
reasonable-looking decision at the time.

| The old file | Lines | What killed it |
|---|---|---|
| 01-crm-operating-spec.md | 487 | Held Notion record ids, view names, and per-inbox send counts. Every CRM change was also a doc edit, so the doc was wrong between the change and the edit — which was always. |
| 02-the-offer-first-five.md **and** 02-the-offer-gso-v2.md | 382 + | Two files, one number. The offer forked rather than changed, and after that neither file was the answer. |
| 03-targeting-and-sourcing.md | 214 | Price floors inline. A real commit in this history is *"Sweep the last stale prices and rename the guarantee everywhere"* — that sweep is what a doc set costs when values live in prose. |
| 04-the-outreach-method.md | 260 | Grew RETIRED-dated sections instead of losing them. A live doc became an archive with a live section in it, and a reader could not tell which was which. |
| 05-the-named-fifty.md | 109 | **Nothing. It aged fine.** It stated a decision and its reason and held no value anything else owned. |

One file out of five survived contact with a normal month, and it survived by
following the rule at the top of this page before anyone had written the rule
down.

**Note how those filenames are written: plain, not in backticks.** That is a
convention the check discovered on its first run, and it is worth keeping. **A
backticked path is a claim that the file exists.** A file that has been deleted
still has a name, and naming it is a record rather than a pointer — so it goes in
plain text, and nothing goes looking for it.

## The four layers

Every fact about this operation lives in exactly one of these. Knowing which one
is how you know where to write something.

| Layer | Where | Changes | Rule |
|---|---|---|---|
| **Constitution** | `docs/spec/` | only by decision | states decisions and reasons; holds no borrowed values |
| **Implementation** | `CLAUDE.md`, `.claude/skills/`, module docstrings | with the code | describes how the current code works; may go stale in a way the tests catch |
| **State** | Airtable, `data/contacted-before.csv`, `out/` | hourly | the live values; never duplicated upward |
| **Narrative** | `docs/journal.md` | append-only | what happened and why, dated; **never** a description of how things are now |

The layer that gets confused most often is constitution against narrative. A
decision belongs in `docs/spec/07-decisions.md`; the session where it was made
belongs in the journal. Both, usually — the journal says *we decided X today and
here is what it cost*, the spec says *X, and here is what would reverse it*.

**The journal is exempt from every check on this page.** It is a log. It
legitimately names deleted files, retired commands and copy lines that no longer
exist, because it is recording that they were deleted. As its own standing
guidance puts it: *that is a record, not a pointer, and it stays.*

## The header block

Every file in `docs/spec/` opens with one, directly under the provenance line.
It is visible prose rather than a comment, because the person most likely to
break the contract is the person editing the file, and a comment is the one
thing they will not see.

```markdown
**Owns:** the values and decisions this file is the authority on.
**Defers to:** `some/authority.csv` — what it owns; `docs/spec/0N-other.md` —
what that one owns.
**Allows:** `SOME LITERAL` — why this file may carry a value it does not own.
```

`Owns:` and `Defers to:` are required. The literal `none.` is a legal value for
either, so a file that defers to nothing has *said so* rather than forgotten.

**`Allows:` is the escape hatch, and it is built to expire.** Each entry is an
exact literal, never a pattern, with the reason attached. An allow that no longer
matches anything in its own file is reported as `STALE ALLOW` — so an exception
dies with the sentence that needed it, instead of quietly accumulating into a
second, invisible spec.

Reach for `Defers to:` before `Allows:`, always. The tempting case is a number
owned by code: naming the module is correct and copying the number under an
allow is the failure mode wearing a permission slip. `docs/spec/07-decisions.md`
carries the worked example.

## The set

| File | Owns | Moves when |
|---|---|---|
| `docs/spec/00-index.md` | this contract | the rules of the doc layer change |
| `docs/spec/01-operation.md` | the business and its real constraint | the shape of the business changes |
| `docs/spec/02-icp.md` | the three floors and the captured fields | the market read changes |
| `docs/spec/03-offer.md` | the money model, and **every price** | the offer or a price changes |
| `docs/spec/04-email.md` | the email as an artifact | the copy rules change |
| `docs/spec/05-pipeline.md` | the stage contracts | a stage's contract changes |
| `docs/spec/06-state.md` | who owns which value | a value moves house |
| `docs/spec/07-decisions.md` | the do-not-re-litigate log | a decision is made or reversed |

Read in order once. After that, the point of the numbering is that a change
lands in exactly one file and you can tell which from the table above.

### The companion specs

Three files outside this directory are part of the defining layer and are not
moving, because they are already correct and already referenced:

- `docs/START-HERE.md` — the front door. One page, the whole machine.
- `docs/hook-rules.md` — the full spec for beat 1, which is the only beat written
  from scratch per lead.
- `docs/agent-orchestration.md` — the worker/verifier chassis, and the return
  contract every agent honours.

And one that is evidence rather than spec: `docs/claude-docs/uae-market-study-2026-07.md`
is the market read `docs/spec/02-icp.md` rests on. It is a dated snapshot of
buyers, not a description of anything that runs.

## Changing a spec

1. **Change the authority first**, if the change is really a value. Editing a
   spec to match a number you have not changed yet gets the doc right and the
   machine wrong.
2. Edit exactly one file. If the change wants to land in two, the boundary is
   wrong — fix the boundary, in this file, as its own change.
3. Say what would reverse it. A decision with no reversal condition is a
   preference, and preferences do not belong in a constitution.
4. Run `python main.py doc-check`.
5. Add a dated entry to `docs/journal.md`. A spec change is exactly the kind of
   thing a future session needs the reason for.

## The check

`python main.py doc-check` enforces the mechanical half of this page: that every
command a doc names exists in the parser, every path it cites is on disk, every
copy-line id is in the CSV, every `Defers to:` target resolves, every spec file
has a header, no file but `docs/spec/03-offer.md` carries a price, and no
`Allows:` outlives its sentence. It fails closed — a docs tree it cannot read is
a failure, never a pass.

It is wired into the test suite rather than into a batch run. A doc typo must
never be able to halt a real send file, because a gate that can do that is a
gate people learn to route around, and then it protects nothing.

## What it cannot do

Be honest about the half that is still on a person:

- **It checks that a pointer resolves, not that a sentence is true.** A doc can
  name every file correctly and still describe a machine that stopped working
  that way in April.
- **It cannot tell a decision from a habit.** Something in
  `docs/spec/07-decisions.md` that nobody has questioned in six months may be
  load-bearing or may be inertia, and the file cannot tell you which.
- **The boundary between files is a judgement, and it will be wrong somewhere.**
  The tell is a change that wants to be made in two places at once. When that
  happens, move the boundary rather than making the change twice.
