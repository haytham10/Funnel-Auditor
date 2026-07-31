# The outbound machine

> **Lost? Read `docs/START-HERE.md`.** One page: what is sold, what the email
> is, the machine in one line per stage, and the checks that fail closed. This
> file is the full map.

A raw list of UAE coaches goes in. A Smartlead upload file comes out, one row
per lead, carrying an email written for that person and mechanically checked
before it was allowed into the file.

**The machine ends at a file.** It does not send. Smartlead owns the inboxes,
the warmup, the ramp, the sequence steps and the replies. Haytham uploads.

## What is sold

The email offers **ten names** — real people who fit their buyer profile, already
pulled, handed over on a fifteen-minute call along with why those ten and not
the other forty. That is the entire ask. No price appears in any email.

The paid offer lives on the call, not in the inbox. Nothing in the machine
quotes a number.

## Why it was rebuilt (so nobody re-litigates it)

Two systems merged on 2026-07-31.

**The funnel auditor** ran 589 leads and made zero. Its diagnosis: it sold a
finding, and a finding in an inbox is a free fix — 4 of 9 engaged leads read it,
fixed it themselves and left. Its reply rate was fine (7-9% against a 1-5%
benchmark); reply to call was 0 of 9. What survived is its chassis: fail-closed
Python gates, worker/verifier orchestration, and the email-verification layer.
The audit, the walk, the findings and the Gmail sending are gone.

**The cold-email system** had the right ingredients — a proof-based identity
beat, a concrete offer, a real CTA — and a pipeline with no repo, no state, and
beats stapled together mechanically so the hook never connected to the paragraph
after it. What survived is its copy and its offer. Its pipeline did not.

The merge point: **the hand-written lines became the drafting model's anchor,
and a deterministic linter made that safe.**

## The machine, one line per stage

```
intake      raw CSV -> Leads, junk stripped, platform URLs routed to social
dedupe      name/domain BEFORE any paid call; email again after research
fetch       free local HTTP first; ONE batched Apify run for what it can't read
research    research-worker per slice -> typed objects, schema-validated
hook        hook-worker proposes -> hook-verifier re-fetches the citation
draft       draft-worker writes against the anchors -> draft-verifier reads cold
lint        every check that can be mechanical, failing closed
export      leads.csv (8 Smartlead columns) + preview.txt + wall-additions
```

`outbound-batch` runs the whole thing. `outbound-draft` is the single-lead and
repair path.

## Hard rules

- **Never send an email.** The machine ends at a file. Sending is Smartlead,
  triggered by Haytham.
- **Never log in to, act as, or automate anything through Haytham's own
  accounts on any platform.** Read-only, no-login tools only. This is an
  identity rule, not a platform ban: public data through a no-login third party
  is fine, on LinkedIn and Instagram the same as anywhere.
- **Never invent a hook.** It is a citation or it is nothing. A hook that cannot
  be re-fetched and confirmed means the lead holds and gets no row. No hook
  found is a good answer.
- **Never invent a number, and never relabel one.** Every number in an email
  must be true of a real client result in `copy/results.csv`. A number sitting
  next to a named segment must belong to that segment: widening to "coaches
  here" is honest, calling a Business result a health coach's is not. Enforced
  by `python main.py lint`, which fails closed.
- **Dedupe runs before any paid call.** Name and domain first, email after
  research. The old pipeline deduped last and paid for eight Apify calls on an
  already-excluded lead. **A warm-thread hit stops the run.** A cold opener
  landing on a live conversation is the only failure here that destroys
  something rather than wasting something.
- **No agent certifies its own work.** Every stage that makes one consequential
  claim has an independent verifier that never saw how the claim was reached,
  and defaults to rejecting it. See `docs/agent-orchestration.md`.
- **The preview is the gate.** No automated check replaces reading ten emails in
  full before uploading. The linter catches invented numbers and lost claims; it
  cannot catch a hook that lands wrong on a specific person.
- **Copy rules, every email:** no em-dashes. No operator jargon (funnel,
  conversion, audit, sequence). No weak closers. Sign off "Haytham". Numbers with
  separators. No gendered pronoun in an identity line.
- **Change a command, change `docs/spec/05-pipeline.md` in the same commit.**
  `doc-check` makes that mechanical rather than a thing to remember. The same
  rule in the other direction: a defining doc never copies a value that code, a
  CSV or Airtable owns — it names the owner. See `docs/spec/00-index.md`.

## The gates (all fail closed, all quotable)

Skills run these and quote the literal output line rather than paraphrasing it.

- `python main.py qualify <lead.json>` — the three floors. **`unclear` passes;
  only a clear `no` drops a row.** A false kill is permanent and invisible; a
  false pass costs one research call.
- `python main.py research <obj.json>` — schema. Catches a verdict outside the
  enum, and a hard yes/no with no source, which means it was reasoned rather
  than fetched.
- `python main.py lint <drafts.json>` — traceability, claim preservation, the
  bridge, voice, and batch repetition.
- `python main.py export --anchors <deal.json>` — the drafts really used the
  lines the batch deal assigned, checked on both the reported id and the written
  text. A drafter that drew its own line ships an email that reads perfectly and
  a CRM row naming a sentence the reader never saw.
- `python main.py email-check|email-verify|email-enrich` — address shape,
  deliverability, and the no-address fallback on their own branded domain.
- `python main.py dedupe` — exits 1 on a warm hit, exit 2 if the wall is
  unreadable. A missing wall file must never read as "nobody has been contacted".
- `python main.py copy-sync` — pulls the hand-written lines out of Airtable and
  **rejects any that fail the linter**, so an edit there cannot break an email.
  Writes nothing when anything fails.
- `python main.py wall-add` — appends a shipped batch to the wall. Run it AFTER
  uploading, never before: walling a lead who never received anything would
  silently exclude them from every future batch. Idempotent.
- `python main.py copy-usage` — reports which lines actually shipped back to
  Copy Assets. Also after uploading. **Additive, not idempotent** — run once
  per batch.
- `python main.py doc-check` — the docs against the code they describe. Every
  command a doc names must exist in the parser, every path it backticks must be
  on disk, every copy-line id must be in the CSV, every `Defers to:` must
  resolve, and **no defining doc but `docs/spec/03-offer.md` may carry a
  price**. Exit 1 on drift, exit 2 if it cannot read the docs. It runs with the
  test suite, not with a batch — a doc typo must never be able to halt a real
  send file.

## The ICP

Three hard floors, and that is all: **UAE-based** (based here, not merely
serving here), **actually a coach**, **active in the last 30 days**.

Captured but never gated on: `coach_type`, `sells_to`, `audience_size`,
`top_program_price_aed`, `solo`. Two of these used to be floors and both were
wrong for different reasons — audience decoupled from the offer the moment we
started selling their clients rather than leverage on their list, and a price floor
reads `unclear` on ~94% of the market, which is a coin flip with extra fetches
attached.

`coach_type` picks the identity line, so it matters: **LinkedIn wins when the
site disagrees.** `sells_to` is collected from their own words, never inferred —
an empty answer draws a generic line, which is weaker than an exact match and
much stronger than a wrong one.

## How lines get chosen

**A batch is dealt, not rolled.** `python main.py deal` allocates the whole
batch at once so the declared weights actually hold. Per-lead hashing is
unbiased only in the limit: measured on the live lines, a 50-lead batch gave one
offer line 8% against a declared 20% and pushed another to 38%, over the
repetition cap. It converged near n=200, and batches are not that big. Dealing
gets the worst miss to about 1 point. `python main.py anchors` keeps the
per-lead draw for single-lead work, where there is no batch to balance against.

**The repetition cap outranks the 70/30 exact-match ratio.** When a segment has
too few identity lines to spread its share — Executive has exactly one usable
for an individuals-facing lead — the excess spills to generic rather than
putting one sentence in front of 70% of a batch. `deal` then prints a `THIN`
line naming the segment and how many more lines it needs. That is the fix; the
spill is the workaround.

## Key pieces

Pointers, not manuals. Every module carries a full docstring.

**`outbound/`** — `normalize` (raw row to Lead, junk classification),
`dedupe` (the two passes and the Contacted-Before wall), `fetch` (the free-first
ladder and the batched Apify plan), `qualify` (the three floors, evidence-
carrying), `research` (the typed contract every worker returns), `anchors` (the
deterministic line draw and the fact table), `lint` (the checks), `export`
(leads.csv and preview.txt).

**`audit/`** — what survived the pivot: `email_check`, `email_verifier`,
`email_enrich`, `apify` (cost-gated), `extract`, `urls`, `draft_lint`,
`footprint`.

**`copy/`** — Haytham's hand-written lines. `identity.csv`, `offer.csv`,
`cta.csv`, `ps.csv`, and `results.csv`, which is the fact table every number in
every email traces back to. **Edit the lines in Airtable, then run `copy-sync`,
which validates and regenerates these files.** `results.csv` is repo-only on
purpose: the lines are voice and get tweaked, the results are audited evidence
and should not be casually editable.

Adding a line is three cells — Beat, Line, Weight. `Line ID` generates from the
text if left blank and `Word Count` is computed, so neither is something to get
wrong. **Weight is a relative share on any scale**; blank means an equal share.
It replaced hand-maintained roll ranges, where adding a fifth line meant
renumbering the other four to keep the spans contiguous.

**`docs/spec/`** — the defining layer, eight numbered files: the operation, the
ICP, the money model, the email, the pipeline contracts, who owns which value,
and the decision log. Its one rule is that **a defining doc states a decision
and its reason and never holds a value something else owns** — where a value
lives in code, a CSV or Airtable, the doc names the authority instead of copying
it. `docs/spec/03-offer.md` is the sole authority on price and the only one
allowed to carry a number. `doc-check` enforces the mechanical half. Start at
`docs/spec/00-index.md`, which also records how the previous project's doc set
rotted, so nobody rebuilds it.

**`data/contacted-before.csv`** — the dedupe wall. In the repo rather than a CRM
because it is read on every run, never needs a view or a filter, and a network
hop is a strange dependency for the cheapest and most consequential check here.
Appending is a commit, so the wall has a history for free.

**Skills** — `outbound-batch` (the whole run), `outbound-draft` (one email, and
the voice references). **Agents** — `research-worker`, `hook-worker`,
`hook-verifier`, `draft-worker`, `draft-verifier`.

## Environment

- **The repo's `.claude/skills/` is authoritative** — never a remembered or
  globally-installed copy. A SessionStart hook fingerprints every on-disk
  SKILL.md; if the `v=` differs from what you recall, the file on disk wins.
- **Cross-session memory is `docs/journal.md`.** The container is ephemeral.
  When a session does anything worth remembering, add a dated entry at the top
  and commit it.
- **Firecrawl is gone** (2026-07-31). The fetch ladder is: local
  `requests` + BeautifulSoup, then the agent's own WebSearch/WebFetch, then
  Apify for what is genuinely login-walled.
- **Apify** needs `APIFY_TOKEN`. Every run is cost-gated at $0.10 and blocks
  with `APPROVAL REQUIRED` / exit 3 above it. **Check the budget once per batch,
  not once per worker.** Container boot dominates the bill, not pages — batch
  every URL into one run.
- **Email verification** defaults to Apify/MillionVerifier, auto-falling back to
  ZeroBounce (`ZEROBOUNCE_API_KEY`) when Apify is near cap. Force with
  `EMAIL_VERIFY_PROVIDER=zerobounce`.
- **Airtable** is the CRM. Base `appejF07kunksqt4D` ("Outbound Machine"):
  Leads `tbl51dU7ojrxCVfxZ`, Batches `tbl97PsqhdndK14hP`, Copy Assets
  `tblnZBHjn430hAB5w`. The old funnel-audit base `appaBExqyEZykb1Qk` is archive
  only, never written to.
- **Reading Airtable from Python** needs `AIRTABLE_API_KEY` (`audit/airtable.py`).
  With a key, bare `copy-sync` fetches directly; `--live` asserts the key rather
  than enabling the fetch. Without one, the MCP is the model's tool only and a
  skill pipes records to `copy-sync` on stdin, which it says plainly instead of
  printing a JSON error. `anchors.py` tries live, then the last synced snapshot,
  then the CSVs, and **caches for the process** — without that, a 200-lead batch
  made 200 identical requests and would trip Airtable's rate limit.
  `OUTBOUND_COPY_SOURCE=csv` forces the offline path; the test suite sets it.
- **Smartlead** owns sending. No API key here yet; handover is a CSV Haytham
  uploads by hand.
- `pip install -r requirements.txt` to run the machine, `requirements-dev.txt`
  to also run the tests. No browser needed — Playwright went with the crawler.
- **CI runs `doc-check` and the suite on every push and PR**
  (`.github/workflows/checks.yml`). `doc-check` gets its own step even though
  the suite covers it, so a docs drift reports as a named failure printing its
  own line rather than a pytest traceback.
