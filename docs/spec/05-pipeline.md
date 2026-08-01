# The stage contracts

_Written 2026-07-31. This is the doc most exposed to daily change, so it states
contracts rather than behaviour: what each stage is handed, what it guarantees,
and what it refuses. How a stage does its job lives in the module's own
docstring, which is where someone reading the code will actually find it._

**Owns:** the stage boundaries, the exit-code contract, and the orderings that
are load-bearing.
**Defers to:** `outbound/normalize.py`, `outbound/dedupe.py`, `outbound/fetch.py`,
`outbound/qualify.py`, `outbound/research.py`, `outbound/anchors.py`,
`outbound/lint.py`, `outbound/export.py` — the eight stages as implemented;
`outbound/copy_sync.py` and `outbound/doc_check.py` — the two checkers that are
commands but not stages; `audit/apify.py` — the paid fetch layer and its cost
gate; `docs/agent-orchestration.md` — the worker/verifier pattern the agent
stages follow; `docs/spec/04-email.md` — what the drafted artifact must be.
**Allows:** none.

## The exit-code contract

Universal, and pinned by `tests/test_cli_failures.py`. Every gate here is quoted
verbatim by a skill rather than paraphrased, which only works if the codes mean
the same thing everywhere.

| Code | Means |
|---|---|
| **0** | the check ran and passed |
| **1** | the check ran and something failed |
| **2** | the check **could not run** |
| **3** | a paid call needs cost approval |

**Exit 2 is the one that matters.** A missing wall file must never read as
"nobody has been contacted"; a missing docs tree must never read as "no drift".
Every gate fails closed: a check that cannot run is a failure, never a pass.

## The run

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

## The two orderings that are not preferences

**Dedupe runs before any paid call.** Name and domain first; email again after
research has found one. The previous pipeline deduped last and paid for eight
enrichment calls on an already-excluded lead. **A warm-thread hit stops the run**
— a cold opener landing on a live conversation is the only failure here that
destroys something rather than wasting something.

**`wall-add` and `copy-usage` run after the upload, never before.** Walling a
lead who never received anything silently excludes them from every future batch.
`wall-add` is idempotent and safe to re-run; `copy-usage` is additive and is not,
so it runs exactly once per batch.

## The stages

### `intake`
**In** a raw CSV. **Out** normalized Leads. **Guarantees** junk and parked
domains classified rather than dropped silently, platform URLs routed to their
social columns, and unmapped headers reported. **Exit 2** if the CSV cannot be
read.

### `dedupe`
**In** Leads and the wall at `data/contacted-before.csv`. **Out** the clear list
and the hits. **Guarantees** two passes, `--stage early` on name and domain and
`--stage late` on email. **Exit 1** on a warm hit. **Exit 2** if the wall is
unreadable *or empty* — an empty wall is indistinguishable from a broken one, and
guessing costs a live conversation.

### `fetch`
**In** Leads. **Out** site reads, plus one batched Apify plan for what free
fetching could not read. **Guarantees** the ladder is walked in cost order: local
HTTP and BeautifulSoup, then the agent's own WebSearch and WebFetch, then a single
batched paid run. **Guarantees** the batch, not the page, is the unit — container
boot dominates the bill, so every URL goes into one run.

### `qualify`
**In** a research object. **Out** three verdicts with their evidence, plus the
captured fields. **Guarantees** `unclear` passes and only a clear `no` drops a
row. **Exit 1** on a clear `no`. **Exit 2** if the input is not an object or a
date will not parse. Owned by `docs/spec/02-icp.md`.

### `research`
**In** a worker's returned object, or an array of them. **Out** a schema verdict.
**Guarantees** a verdict outside the enum is caught, and **a hard yes or no with
no source named is rejected** — that combination means the answer was reasoned
rather than fetched. This is the stage with no verifier agent on purpose: a
schema check is cheaper than an agent and strictly harder to talk around.

### hook
Two agents, not a command. `hook-worker` proposes with an exact quote, URL and
date; `hook-verifier` re-fetches the citation in a context that never saw the
search and defaults to refuted. **Three verdicts, not two** — INCONCLUSIVE holds
the lead where it is rather than killing it. **No hook found is a good answer**:
the lead holds and gets no row. `docs/hook-rules.md` owns the rest.

### draft
`draft-worker` writes against the four dealt anchor lines and runs the linter on
its own output; `draft-verifier` reads the finished email cold and judges the one
thing no linter can check.

### `anchors` / `deal` / `facts`
`deal` allocates a whole batch at once so the declared weights hold; `anchors`
keeps the per-lead draw for single-lead work, where there is no batch to balance
against; `facts` prints the client-result table and the numbers it licenses.
Owned by `docs/spec/04-email.md`.

### `lint`
**In** drafts. **Out** a pass or a list of failures. **Guarantees**
traceability, claim preservation, the bridge, voice, and batch repetition.
**Exit 1** if any draft or the batch check fails. Everything fails closed — a
check that cannot run is a FAIL.

The identity beat gets a second, tighter gate on top of the widened number
check: it is written per lead, so what is fixed about it is its **claim**, not
its words. See the anchor contract in `docs/spec/04-email.md`, which owns that
decision. A draft with no claim behind it is warned about rather than skipped
silently, because a PASS line looks identical either way.

### `export`
**In** drafts. **Out** `out/leads.csv`, `out/preview.txt`,
`out/wall-additions.csv`, `out/line-usage.csv`, `out/rejected.txt`.
**Guarantees** an email that failed the lint is *absent* from the upload file,
not flagged in it; and that all five outputs are cleared first, so a blocked
batch cannot leave a stale uploadable file behind. `--anchors` additionally
checks the drafts really used the lines the batch deal assigned, on both the
reported id and the written text.

It also re-checks each identity sentence against the claim **in the deal file**,
which is a separate finding from the line check for a reason: one answers *which
line*, the other *what the sentence claims*, and a combined message would send a
drafter looking in the wrong place. The deal is the authority rather than the
draft, because the drafter's own lint run resolves the claim from what the
drafter reported — which is the worker checking its homework against its own
answer sheet. A deal carrying no claim is a rejection, not a skip.

**The eight Smartlead columns:**

```
email, first_name, last_name, website, linkedin_profile, location, subject, body
```

Six are Smartlead's own native lead fields; `subject` and `body` arrive as custom
fields and are used in a campaign step as template variables. **It is
`linkedin_profile`, not `linkedin_url`** — the wrong spelling still imports
successfully and silently lands as an extra custom variable, which is the worst
kind of wrong.

### `copy-sync`
Pulls the hand-written lines out of Airtable and **rejects any that fail the
linter**, so an edit there cannot break an email. It is a gate, not a copier:
when anything fails it writes nothing at all.

An identity line must also declare a Claim that resolves, and must satisfy it —
the same check the drafted email gets, run against the hand-written line. A bank
line that cannot pass its own claim condemns every email dealt it, and the
drafter is then asked to satisfy something impossible with one rewrite pass. And
a totalising clause about the meetings needs a qualifier a column backs, which
is the only thing that separates "every one with somebody who could sign off"
from "all with prospects ready to say yes". That second rule is a heuristic over
English and it says so in its docstring: it will miss a flourish phrased without
a totaliser, and it cannot judge truth, only sourcing.

Both hard-fail rather than warn. A blocked line costs one person one minute with
the line in front of them, which is the cheapest place in the whole machine to
pay, and this command's output is mostly green so a warning in it is one nobody
reads.

### `copy-check`
**In** nothing. **Out** whether Airtable is what a batch would actually draw
from. **Guarantees** the live Copy Assets lines pass the linter, and that the
committed cache under `copy/` still matches them. **Exit 1** on either, **exit
2** when the table could not be read at all.

The counterpart to `copy-sync` and deliberately not the same command: that one
writes, this one only looks, so it is safe at the top of a batch and again after
a fix. **Airtable owns every line; `copy/*.csv` is a cache of it.** Two failures
put a stale line in a stranger's inbox, and both used to be silent — a live edit
that fails the linter (the bank falls back, so the edit looks applied and the
batch ships the previous copy), and a cache nobody regenerated. `deal` enforces
the same thing at the moment lines become a batch's lines: it exits 1 on a
rejected live edit with no override, and exits 1 on an unreadable table unless
`--allow-cached-copy` says to accept the cache on purpose.

### `wall-add` / `copy-usage`
After the upload. See the ordering rule above.

### `email-check` / `email-verify` / `email-verify-batch` / `email-enrich`
Address shape and DNS deliverability (free), a paid deliverability confirm, the
same confirm batched for a whole slice's addresses in one call, and the
no-address fallback on the lead's own branded domain. The fallback converges
on exactly one address, never auto-passes a catch-all domain, and refuses free
provider domains.

**One paid verifier, one free fallback, and the fallback says what it is.**
`audit/apify.py` owns which actor `email` names. `EMAIL_VERIFY_PROVIDER` picks
between it and the local check, and a capped Apify quota switches to the local
check on its own. The local check reads syntax, the never-send and typo and
disposable lists, and MX — so it can prove a domain takes mail and never that a
mailbox exists. Its best answer is a WARN that says so, and it can never clear
an address for sending by itself. Its FAILs are real.

**`email-verify-batch` is the only place a verifier outage is visible**, because
an outage is a property of the run rather than of any address in it. Every
address in a batch coming back inconclusive is not an address pattern; it exits
2, the code for a gate that could not complete, rather than 1, which would be a
claim about the addresses. This exists because a dead actor answered "error" for
40 consecutive leads and read to the operator as a long run of catch-all
domains.

**Every row names who answered it**, and `verify-email` returns one row per
address asked about — an address the actor did not answer on comes back as
`no_result` rather than being dropped from the list.

### `apify`
The no-login third-party fetch layer, and the only paid one. Subcommands:
`apify limits` (check the budget **once per batch**), `apify actors`,
`apify ig`, `apify ig-post`, `apify li-posts`, `apify li-profile`,
`apify youtube`, `apify verify-email`, `apify search`, `apify footprint`.

`apify li-profile` and `apify verify-email` take one target or several; several
is one actor run for the whole batch rather than one per lead (`li-profile`
correlates results back to each url even if the actor drops one; `verify-email`
already batches under `email-verify-batch`). `apify li-posts` stays one call
per profile on purpose — the actor's `maxPosts` is a budget shared across every
url in the run rather than a per-profile cap, confirmed by direct test (two
target urls, one shared cap, all posts came back from a single profile).
Batching it would silently starve most leads of post data rather than save
anything worth that risk.

Every run is cost-gated and **exits 3** above the ceiling rather than spending.
The ceiling itself lives in `audit/apify.py` and is not restated here.

### `classify-footprint`
Merges pre-fetched search hits into sourcing candidates. Fetch-agnostic by
design — it never calls a search API itself.

### `doc-check`
**In** nothing. **Out** the docs checked against the code they describe.
**Guarantees** every command a doc names exists in the parser, every path it
cites is on disk, every copy-line id is in the CSVs, every `Defers to:` target
resolves, every spec file has its header block, no spec file but
`docs/spec/03-offer.md` carries a price, and no `Allows:` outlives the sentence
it was written for. **Exit 1** on drift, **exit 2** if it could not run.
Owned by `docs/spec/00-index.md`.

It also checks the one value in this operation whose authority is not in the
repo: the CRM's select options, which `audit/airtable.py` and the two segment
lists mirror and Airtable owns. That check leaves the machine, so it runs only
when a key is set, and reports itself as skipped when there is none — CI has no
key. `doc-check --live` makes a missing key **exit 2** instead of a skip, the
same assertion `copy-sync --live` is. A schema it could not fetch is exit 2, not
a pass.

That half also runs on its own, without being asked:
`.claude/hooks/schema_drift.py` fires on a `git push` from a Claude Code session
— where a key exists and where the pull request is opened — and blocks the push
on drift.

## What is unknown

- **The tier-0 fetch rate is unmeasured.** Nobody has published what share of
  coach sites a plain HTTP fetch can read, and every cost estimate downstream
  depends on it. The first real batch measures it.
- **The real Apify bill has never been reconciled against a run.** The last paper
  estimate was wrong by most of an order of magnitude.
- **Follow-ups are not built.** Touches two and three are Smartlead sequence
  steps, and nobody has decided whether they should be personalised per lead.
- **Sourcing is phase two.** Today the machine starts from a list somebody drops
  on it.
