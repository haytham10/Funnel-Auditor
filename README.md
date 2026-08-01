# The outbound machine

A raw list of UAE coaches goes in. A Smartlead upload file comes out, one row per
lead, carrying an email written for that person and mechanically checked before
it was allowed into the file.

**It does not send.** The machine ends at a file. Smartlead owns the inboxes, the
warmup, the sequence steps and the replies.

```
intake -> dedupe -> fetch -> research -> hook -> draft -> lint -> export
                                                                    |
                                            out/leads.csv + out/preview.txt
```

## Quickstart

```bash
pip install -r requirements-dev.txt   # or requirements.txt to just run it
python main.py doc-check              # the docs against the code they describe
python -m pytest -q                   # the suite, doc-check included
```

`pytest` is in `requirements-dev.txt`, not `requirements.txt` — running the
machine does not need it. Every test file also runs standalone
(`python tests/test_lint.py`), so the suite works either way.

Both of those commands run on every push and pull request
(`.github/workflows/checks.yml`).

Run a whole list end to end by handing a CSV to the `outbound-batch` skill. For
one email, or to repair one, use `outbound-draft`. Both live in
`.claude/skills/` and that copy is authoritative.

## The gates

Python owns every check; the model owns the words. Every gate fails closed, and
prints one line meant to be quoted verbatim rather than paraphrased.

| Exit | Means |
|---|---|
| 0 | the check ran and passed |
| 1 | the check ran and something failed |
| 2 | the check **could not run** |
| 3 | a paid call needs cost approval |

Exit 2 is the one that matters. A missing dedupe wall must never read as "nobody
has been contacted".

```bash
python main.py qualify  <lead.json>     # the three floors; `unclear` passes
python main.py research <obj.json>      # the schema: no verdict without a source
python main.py dedupe   <leads.json>    # exits 1 on a warm-thread hit
python main.py lint     <drafts.json>   # invented numbers, lost claims, voice
python main.py export   <drafts.json>   # writes only what passed
python main.py doc-check                # the docs against the code
```

`python main.py --help` lists the rest. `docs/spec/05-pipeline.md` says what each
one guarantees, and `doc-check` fails if a command exists that nothing documents.

## Layout

```
main.py            the CLI — every command is a decision, printed as a line
outbound/          the eight stages, plus copy_sync and doc_check
audit/             what survived the pivot: email checks, Apify, extraction
copy/              a cache of Airtable's Copy Assets, plus the client-result facts
data/              the dedupe wall — who has already been contacted
docs/spec/         the defining layer (start at 00-index.md)
docs/              START-HERE, hook rules, agent orchestration, the journal
.claude/           the skills and the worker/verifier agents
tests/             the suite; every file also runs standalone
```

## Where to read next

- **Lost?** `docs/START-HERE.md`. One page, the whole machine.
- **What is actually decided, and why?** `docs/spec/` — the operation, the ICP,
  the money model, the email, the pipeline contracts, who owns which value, and
  the decision log. Its index is `docs/spec/00-index.md`.
- **Working on the code?** `CLAUDE.md`, then the module docstrings. Every module
  carries a full one, and it is where the reasoning lives.
- **What happened when?** `docs/journal.md`, newest first.

## Environment

Nothing is required to run the free path — the fetch ladder spends local HTTP
and the agent's own search before it spends anything.

| Variable | For |
|---|---|
| `APIFY_TOKEN` | the paid, no-login fetch layer. Cost-gated, blocks above the ceiling |
| `AIRTABLE_API_KEY` | reading the CRM and the copy bank from Python. Airtable owns every line; without a key the machine draws from the cache in `copy/` and says so |
| `EMAIL_VERIFY_PROVIDER` | `apify` (default) or `local`. The local MX check needs no key and never claims a mailbox exists |
| `OUTBOUND_COPY_SOURCE=csv` | pin the copy bank to the committed CSVs. The test suite sets this |

## Two rules no code enforces

Everything else here is checked by a gate. These two are on a person:

- **Never send from the machine.** Sending is Smartlead, triggered by hand.
- **Never log in to, act as, or automate through Haytham's own accounts,
  anywhere.** Public data through a no-login third party is fine; the machine
  wearing his face is not.

And one instruction no check replaces: **read `out/preview.txt` in full before
uploading.** The linter catches invented numbers, lost claims and repetition. It
cannot catch a hook that lands wrong on a specific person.

## Status

The machine runs end to end and has produced real batches. What it has not done
is close anything: **reply-to-call has never been above zero**, the offer behind
the call has never been sold, and the tier-0 fetch rate that every cost estimate
depends on is unmeasured. Those are stated as open bets in
`docs/spec/01-operation.md` rather than buried.
