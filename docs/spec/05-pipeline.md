# The stage contracts

_Written 2026-07-31. This is the doc most exposed to daily change, so it states
contracts rather than behaviour: what each stage is handed, what it guarantees,
and what it refuses. How a stage does its job lives in the module's own
docstring, which is where someone reading the code will actually find it._

**Owns:** the stage boundaries, the exit-code contract, and the orderings that
are load-bearing.
**Defers to:** `outbound/normalize.py`, `outbound/dedupe.py`, `outbound/fetch.py`,
`outbound/resolve.py`, `outbound/plan.py`, `outbound/select.py`,
`outbound/qualify.py`, `outbound/research.py`,
`outbound/anchors.py`, `outbound/lint.py`, `outbound/export.py` — the eleven
stages as implemented;
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
resolve     which channels are plausibly theirs, typed and evidenced. Advisory
plan        which hook rungs a lead has, and what each would cost. Advisory
research    research-worker per slice -> typed objects, schema-validated
hook        hook-worker proposes -> hook-verifier re-fetches the citation
select      which observation a hook would come from, without fetching. Advisory
draft       draft-worker writes against the anchors -> draft-verifier reads cold
lint        every check that can be mechanical, failing closed
export      leads.csv (8 Smartlead columns) + preview.txt + wall-additions
```

Every fetch along that line writes itself to `data/runs/<batch>.jsonl` as it
happens, so a batch that dies in stage 3 still leaves its accounting.

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

**Tier 0 is concurrent.** It was a serial loop, and on 151 sites at a
15-second-per-page timeout it exceeded a 120-second ceiling, then a 590-second
one, and was killed twice before finishing. `--workers` sets the pool; the work
is network-bound and one lead is one thread is one host, so nothing here makes
more requests to any single host than the serial version did.

**The escalation runs only when asked.** `--escalate` executes the plan through
the same cost gate and the same **exit 3** as every other paid call; without it
the plan is printed and nothing is spent. Two vetted actors sit behind it, one
static and one that renders, and which one a URL gets is not a preference: a
browser is only correct for a page that returned 200 with no text. Both are
Apify's own compute-billed actors, so an estimate is genuinely impossible rather
than merely unavailable, and the gate says which of those two it is — one is
worth retrying and the other never will be.

Until 2026-08-01 the plan named an actor id that was in no vetted map, so
nothing could run it through the gate at all; it was something the operator
executed by hand outside the approval path, and the first real batch skipped it
entirely.

**It also names the leads it cannot help with.** A lead with no site produced
no output here, so every research worker met it cold and improvised — which is
how the last batch came to use web search and Instagram without either being a
rung anybody had planned. The report now prints a `SEARCH` line per lead with
no site and no social, and an `IG` line per lead reachable only on Instagram.
That is handed-out work rather than a gap each worker rediscovers.

**And it says which sites never mention the lead.** About 40 of 151 rows on the
first batch pointed at somebody else — parked domains, name collisions, a
coach's training school, an Ohio retreat house, a Dutch tech-news site. Nothing
checked, so each was found by a worker, by hand, after the fetch had been paid
for. `OWNER-CHECK` is one line naming all of them before any money is spent.
**Advisory, never a kill**: a real coach's site may carry only a brand name, and
a false kill here is permanent and invisible. `intake` does the free half of the
same check on a LinkedIn or Instagram handle, and records it as a note. Both are
the prose presentation of the rule `resolve` returns a verdict for; the handle
extraction and the match live in `outbound/resolve.py` and are called from
`intake`, not copied into it.

**A lead whose only URL is a platform produces nothing here.** `fetch` targets
the site column, and a podcast show or a link-in-bio page is routed to social
research rather than treated as an own site, so such a lead is in neither the
`IG` nor the `SEARCH` line. `resolve` is where it reappears: it emits an Identity
for every lead and names the ones free retrieval cannot help with.

**And it counts what reading the homepage first would have saved, without
saving it.** `HOMEPAGE-FIRST` names how many leads were already a clear `no` on
page 1 and how many page fetches past that page were therefore avoidable. Every
page is still read; this is a number, the same way `plan` and `select` shipped
computing an answer nothing consumes.

It is a measurement rather than a change because **the −30% the proposal
estimated does not survive contact with the code.** That figure reasons from 106
of 151 leads passing the floors, but those failures were settled with everything
a research worker gathered across several sources, and the floors pass on
`unclear`. Skipping anything here needs a clear `no` from one page, and the two
floors only reach `no` on positive contrary evidence — a named non-UAE location,
or a named non-coach occupation. The honest claim is that nobody knows how often
that happens, and one batch says. The floors themselves are not restated here:
`fetch` calls `outbound/qualify.py`'s, which own them.

### `resolve`
**In** Leads, plus the site read from `fetch --out`. **Out** one `Identity` per
lead: its channels, each with a `confirmed | absent | unknown` verdict and the
evidence that settled it, and the site's own owner verdict passed straight
through. **Guarantees** every lead gets an Identity, including a lead with no
channels at all. **Exit 2** if the leads or the sites file cannot be read,
**exit 1** only if its own output fails its own schema. Owned by
`outbound/resolve.py`.

**It gates spend, never inclusion.** Being advisory is right for a *kill* — a
false kill is permanent and invisible — and wrong for a *purchase*. About 40 of
151 rows on the first batch pointed at somebody else, and nothing stopped the
machine paying to scrape a different person with the same name. Nothing here
declines anything yet; a run where every channel is `absent` exits 0, and it
always will. The ownership verdict must never become a reason to skip a lead.

**`unknown` never means the tell said no.** It means no tell was available. A
handle mismatch is the only path to `absent`, so an opaque channel id —
`youtube.com/channel/UC1a2b3c` — is `unknown`, not a bad row. Without that rule
the report fills with false negatives and becomes the line people scroll past,
which is the failure `OWNER-CHECK` was built to fix.

**It runs after `fetch`, and that is a decision.** The proposal's diagram puts it
first, but that diagram has no `fetch` stage at all — tier 0 is absorbed into a
later phase there. In the machine as it stands, resolving first would mean
reading each homepage and then reading it again in `fetch`. See D22 in
`docs/spec/07-decisions.md`.

**Nothing consumes an Identity yet.** Additive, in the posture the ledger and the
observation contract shipped in.

### `plan`
**In** the identities from `resolve --out`, and optionally the Leads, which are
the only place a lead's own site URL lives. **Out** one `LeadPlan` per lead: the
rungs that are populated for that person, what each would cost, and which paid
ones would be declined. **Guarantees** every lead gets a plan, including a lead
with no rung at all and a lead whose every paid rung would be declined; it
fetches nothing and runs no actor. **Exit 2** if the identity file cannot be read,
**exit 1** only if its own output fails its own schema. Owned by
`outbound/plan.py`.

**The ladder is here rather than in prose, and that is D23.** Where a hook comes
from was two markdown files kept in agreement by hand, and the agreement failed
twice on record. `LADDER` is now the authority; `docs/hook-rules.md` keeps what a
hook is and names this module.

**It declines nothing.** A step whose channel is `absent` is labelled `decline`
and taken anyway. D21 says an ownership verdict may gate a purchase where it may
not gate a kill, and it carries the reversal condition — whether declining costs
more verified hooks than it saves scrapes. That has never been measured, and a
gate shipped alongside its own measurement would generate the data judging it.
`unknown` is never declined: it means no tell was available, not that the tell
said no.

**Pricing is opt-in.** `--price` needs a token and the network. Without it a paid
step reports "not priced", which is a different answer from an estimate of zero
and a different answer again from the cost gate's own "cannot be priced" — and a
batch nobody looked at must never report as a free one.

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

The object may also carry the observations behind those verdicts, and they are
validated here through the same call — capped, so one worker that got an enum
wrong cannot bury the floor violation that actually drops a row. See `observe`.

### hook
Two agents, not a command. `hook-worker` proposes with an exact quote, URL and
date; `hook-verifier` re-fetches the citation in a context that never saw the
search and defaults to refuted. **Three verdicts, not two** — INCONCLUSIVE holds
the lead where it is rather than killing it. **No hook found is a good answer**:
the lead holds and gets no row. `docs/hook-rules.md` owns the rest.

### `select`
**In** research objects, which after the hook stage carry both halves — the
observations the research workers kept, and the hook fields the hook stage wrote
back. **Out** one `LeadSelection` per lead: a ranked shortlist of three
candidates and the ban that excluded everything else. **Guarantees** it fetches
nothing, writes no hook, and never changes which lead is drafted; every lead gets
a selection, including one with no observations. **Exit 2** if the input is not
research objects, **exit 1** only if its own output fails its own schema — a
disagreement is never a failure. Owned by `outbound/select.py`.

**It runs alongside the hook stage, not in place of it.** `hook-worker` still
fetches and is not edited. `--against` is the measurement the phase exists for:
it asks whether the ranker would have picked the same evidence the hook stage
paid for, and reports five verdicts because `missed` and `unobserved` say
opposite things about whether that fetch can be removed.

**Four of the twelve bans stop being something an agent must remember** —
third-party coverage, stale news, generic site copy, and invented specifics,
the last through the `obs_id` join. `docs/hook-rules.md` still owns all twelve.

**A quote found here is not a verified quote.** It is in the text we stored,
which is a different claim from being on the page. The verifier's live re-fetch
is the only mechanism that has caught a fabricated claim, and it stays.

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
`apify verify-email`.

**Two actors were retired 2026-08-01** and their subcommands with them. Neither
was a large bill; both were surface area, which `audit/apify.py`'s own rule says
is the thing to count. The YouTube channel actor returned a subscriber count and
nothing else, and its only consumer was `audience_size` — a field
`docs/spec/02-icp.md` captures and never gates on, so a paid call was wired to a
field that by design changes no decision. The Google SERP actor duplicated the
agent's own free WebSearch, which `audit/footprint.py` already called the
preferred path and which is what every skill actually used.
`classify-footprint` is untouched: it never fetched anything itself.

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

### `observe`
**In** one observation or an array of them. **Out** the schema verdict.
**Guarantees** a record claiming to be something fetched can be checked when it
is written: platform, kind and author inside their enums, a piece of content
carrying its text, a publication date that parses and has already happened, and
a `retrieved_by` naming a rung this machine actually has. **Exit 1** on a
violation, **exit 2** if the input is not an object or an array of them. Owned
by `outbound/observe.py`.

**Additive, and nothing consumes it yet.** A research object may carry
observations alongside its verdicts; no stage reads them, the hook stage still
does its own fetching, and the duplicate that makes unnecessary is left in place
on purpose so `ledger report` can price it. What exists now is the contract and
its gate.

**The point is what research does not do.** Research keeps a `_source` string
per verdict, so the post that settled `active_recent` — the exact material a
hook is made of — is read once, reduced to a boolean, discarded, and paid for
again one stage later.

**`text` is verbatim, and no check can prove it.** That is why it is stated
rather than assumed: a summarised observation reads fine, ranks fine, and yields
a hook whose quote is not on the page — the one failure the independent verifier
exists to catch, arriving through the one door it does not watch.

### `ledger`
**In** a retrieval, or a batch label. **Out** one JSON line per fetch, and the
batch read back. **Guarantees** every retrieval the code made carries what it
was priced at and how long it took, and a second fetch of the same
`(lead, url)` that is not a verification is named. **Exit 2** on a ledger it
could not read, which includes one that is not there — the dedupe wall's
asymmetry, one stage over: a missing wall must never read as "nobody has been
contacted", and a missing ledger must never read as "this batch cost nothing".
**Never exit 1**, not even on a duplicate. Owned by `outbound/ledger.py`.

`ledger add` is the only way a retrieval Python did not make gets recorded. An
agent's own WebSearch and WebFetch happen model-side and are invisible here, so
those lines are **reported on trust** and `retrieved_by` keeps them
distinguishable from the ones the code wrote itself. `ledger report` reads a
batch back and writes nothing.

**Reporting a duplicate is the job; failing on one is not.** A gate that can
halt a real send file over an accounting line is a gate people learn to route
around — the same reason `doc-check` runs with the tests rather than with a
batch. The stage that removes the duplicate is the one that gets to block on it.

**The costs are estimates, and the ledger says so.** The runner uses Apify's
run-sync-get-dataset-items, which collapses a run to its output, so the billed
`usageTotalUsd` on the run object is never fetched. A ledger implying otherwise
would be worse than none.

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
