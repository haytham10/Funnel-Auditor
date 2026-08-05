# The stage contracts

_Written 2026-07-31. This is the doc most exposed to daily change, so it states
contracts rather than behaviour: what each stage is handed, what it guarantees,
and what it refuses. How a stage does its job lives in the module's own
docstring, which is where someone reading the code will actually find it._

**Owns:** the stage boundaries, the exit-code contract, and the orderings that
are load-bearing.
**Defers to:** `outbound/normalize.py`, `outbound/ig_intake.py`,
`outbound/triage.py`, `outbound/dedupe.py`, `outbound/fetch.py`,
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
ig-intake   the same for an Instagram profile dump, which also arrives with the
            posts the paid IG rung would have fetched
triage      RUN / HOLD / DROP before anything is spent. `unclear` is HOLD
dedupe      name/domain BEFORE any paid call; email again after research
fetch       free local HTTP first; ONE batched Apify run for what it can't read
resolve     which channels are plausibly theirs, typed and evidenced
plan        which hook rungs a lead has and what each costs. A decline BINDS
research    research-worker per slice -> typed objects AND the observations
            every later stage reads. The machine's retrieval stage
deal        the four hand-written lines, allocated for the whole batch at once
select      rank the observations -> a shortlist of 3 per lead. No fetching
hook        hook-worker quotes the shortlist and writes the clause -> gated by
            `main.py hook --against` -> hook-verifier re-fetches the citation LIVE
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

**`deal` runs before the hook stage, not after it.** The bank leaves between 12
and 36 words for a hook depending on the draw, and dealing afterwards meant a
hook could be found, verified against a verbatim quote, and then handed to a
drafter with 12 words of room — while `draft-worker` is forbidden from cutting
the four hand-written lines, so the only thing left to compress was the sentence
an independent verifier had just certified. A hook that fits is chosen; a hook
squeezed afterwards is a citation drifting from its source. See D24.

## The stages

### `intake`
**In** a raw CSV. **Out** normalized Leads. **Guarantees** junk and parked
domains classified rather than dropped silently, platform URLs routed to their
social columns, and unmapped headers reported. **Exit 2** if the CSV cannot be
read.

### `ig-intake`
**In** an Apify `instagram-profile-scraper` dataset. **Out** Leads *and*
`observe.Observation` records — the account's own posts, captions verbatim,
with the dates they were published and the URLs they live at. **Guarantees**
every observation passes `observe.validate_all` before either file is written,
`author=self` proven against the post's `ownerUsername` rather than assumed,
and `retrieved_by` naming `apify:ig_profile`, the actor that really produced
the dump. **Exit 1** if any observation fails the schema — nothing is written.
**Exit 2** if the dataset cannot be read or is not an array.

A dump like this is not input to the retrieval stage, it **is** a retrieval,
made outside this repo. `cost_usd` is 0.0 because nothing here paid for it, and
the ledger records what a fetch cost *here*. See D30.

**It is a corpus, not a source list** (D32). Run as the list itself, 237
profiles shipped 2 emails, because on Instagram owning a domain is
anti-correlated with being our ICP and 74% of the coaches had no address
anywhere. Attach it with `corpus attach` to a list that arrives reachable.

### `icf-intake`
**In** an ICF Credentialed Coach Finder export (`.xlsx`). **Out** normalized
Leads *and* a prefill file of the ICP fields the coach filled in themselves,
keyed by `fetch.lead_key`. **Guarantees** the three hyperlink-bearing columns
are read from their targets rather than their text, and that nothing in the
prefill settles a floor. **Exit 2** if the workbook, the sheet or `openpyxl`
cannot be read. **Exit 1** on an unmet `--expect`.

**It exists because this source's load-bearing values are not in its cells.**
`ICF profile` reads the literal string "View profile" in every row and the URL
that reaches the listing lives only in `cell.hyperlink.target`. A CSV conversion
produces a fully-populated column carrying nothing, and it looks fine — which is
`crm-rows`' lesson, where twenty rows went in with no First Name and the check
that passed them looked at four fields and reported 20/20.

**The prefill is a hint file and never a verdict.** A directory listing is the
coach's own words, which is exactly what `sells_to` requires; it is also stale
by construction, so a coach who left the UAE two years ago still reads `Dubai`.
Every value carries `icf_directory` and lives in its own file precisely so no
later stage can mistake it for something a worker fetched. The activity floor is
untouched — it settles on dated observations and this source has none.

Three mappings are decisions rather than transcription, and
`outbound/icf_intake.py` owns them: `Personal and Organizational` maps to `""`
because `qualify.classify_sells_to` already rules that a source saying both says
nothing; `Rate (listed)` is a USD hourly band and never becomes
`top_program_price_aed`, which is an AED program price and a different number;
and the ICF profile URL never becomes `site_url`, because it is a directory
listing and putting it there would point tier-0 fetch at ICF's own page for
every lead on the list.

### `channel-find`
**In** the CLEAR list from `dedupe --stage early`. **Out** a LinkedIn,
Instagram and website verdict per lead, each accepted only with a stated reason
to believe it is theirs. **Guarantees** every query in a chunk goes in one run,
correlation back to leads is on `searchQuery.term` and never on position, and a
lead already carrying a verdict is not re-queried. **Exit 0** when every
searched lead reached FOUND, **1** when any is still open, **2** when the search
layer could not run or `--leads` is missing, **3** for cost approval.

**A URL needs a reason to be believed this lead's, and the stakes are higher
than for an address.** `email-find` shipped without that rule and reported FOUND
four times in five on strangers' addresses. A wrong address at least bounces. A
wrong LinkedIn URL verifies clean, scrapes clean, and produces a real,
re-fetchable, quotable hook about a real person who is not the lead — `hook`,
`hook-verifier` and `lint` all check the content and none of them checks
*whose*. So an uncorroborated URL is a blank field, never a best guess, and
there is deliberately no rule that accepts on circumstance alone.

**Three verdicts leave a field blank and they are different answers.** `NONE`
means nothing was found. `UNCORROBORATED` means something was found and dropped
as probably somebody else's. `AMBIGUOUS` means two or more people of that name
were found and nothing separates them. The first is a fact about the coach, the
second a fact about this filter, and the third is the only one a human could
settle in thirty seconds — which is why it has to be tellable apart. Every drop
is kept with its reason, because the filter is a heuristic and the count is how
anybody notices it going wrong.

**An ambiguous match attaches nothing**, which is `corpus attach`'s rule for
`corpus attach`'s reason. The pilot is why it is here: six of fourteen FOUND
leads came back holding two or three LinkedIn profiles that all carried the
name, and the first was silently kept — for one lead a one-in-three guess
between three real people, shipped as a confirmed channel. The only honest
tiebreak is the vanity slug, since a plain slug is one its owner claimed and a
digit-suffixed one is what LinkedIn generated when the plain one was taken.
Where that does not separate them, nothing does, and the output is a blank field
naming the competitors.

**Without `--execute` the plan is printed and nothing is spent**, including the
exact query strings — `fetch --escalate`'s rule, so a query shape can be read
before it is bought three hundred times. **`--leads` must be the clear list and
its absence is exit 2**, because this is the first command here that spends on a
whole list at once and the hard rule is dedupe before any paid call.

**Chunking is for resume and blast radius, never for evading the gate.** A
chunk of any useful size trips the cost gate every time — `audit/apify.py` owns
the event prices and the threshold, and the ledger records what a run actually
cost. Sizing a chunk to slide under that threshold would be routing around an
approval a human should give once. Resume is a membership test rather than a
chunk counter, so a chunk that died halfway leaves the leads it did answer for.

The state file keeps the raw organic rows beside each verdict, which is
`select --batch`'s rule: a later change to the corroboration rule is re-scorable
against the corpus that produced the first answer, rather than a reason to pay
for the same search twice.

**No AI Overview and no observations.** The overview is not bought here at all —
there is no absence verdict worth paying for, since "this coach has no LinkedIn"
is a fact the organic results state by not containing one. And a SERP snippet
never becomes an `observe.Observation`: a snippet is Google's excerpt, not
verbatim page text, so minting one would put an unverifiable quote into the
corpus `hook-worker` quotes from — the fabrication class `hook-verifier` exists
to catch, arriving through the one door it does not watch.

The logic lives in `audit/channel_find.py` and **fetches nothing**, the same
property that made `audit/footprint.py`'s retirement a deletion rather than a
rewrite.

### `icf-export`
**In** the Leads, the prefill, the channel verdicts and the address verdicts.
**Out** the source workbook with its original columns untouched and the
enrichment appended, a committed CSV, and a `leads.json` carrying the found
channels merged in so `intake` never runs on this list again. **Guarantees**
coverage printed for **every** added column, and that a found website never
overwrites the sheet's listed one. **Exit 1** on an unmet `--expect` or a row
that cannot be joined, **exit 2** on an unreadable input.

**Coverage is printed for every column and not the ones anybody expects**, which
is `crm-rows`' lesson: twenty rows once went into the CRM with no First Name on
any of them, and the check that passed them looked at four populated fields and
reported 20/20. It caught its own version of that here — a "found website"
column reading 117 of 311 that contained 33 discoveries and 84 copies of the
website the sheet already listed.

**Provenance is derived from the Lead, not read off the channel file.** The
`ICF row` / `search` label answers "did we buy this or did it arrive free", and
deriving it from the authority in hand rather than trusting a key the upstream
command might not have written is what makes it true.

### `chunk`
**In** the Leads and the enriched CSV `icf-export` wrote. **Out** four committed
files: three chunks a batch can run, and a held-out record carrying a written
reason per lead. **Guarantees** every lead lands in exactly one group, that the
two halves of the strong pool are equal to within one and balanced on the strata
they are cut on, and that the same seed reproduces the same split. **Exit 1** on
a lead the enrichment does not carry, named. **Exit 2** on an unreadable
enrichment — a file nobody could open is not a list of zero coaches.

**The cut is by evidence, not by row number**, because the leads are not
interchangeable. A dead address produces no row however good the hook is, and a
lead with no channel has nowhere for research to look, so the activity floor
cannot settle and no hook can be cited. Thirds of the file would put a third of
both groups in every chunk and pay for them three times.

**Chunk 1 and chunk 2 are two halves of one pool**, so chunk 1's measured yield
predicts chunk 2's and the second chunk is a decision rather than a hope. The
alternation counter carries **across** strata; resetting it inside each one
hands every odd stratum's extra lead to the same half, which on the live list
produced 67/57 instead of 62/62.

**Held out is not dropped.** Every excluded lead is in the held-out file with
its reason, so a hundred missing rows read as a decision somebody made rather
than an oversight — `qualify`'s rule that a false kill is permanent and
invisible, applied one stage earlier. That file is deliberately **not** shaped
like a leads file: a held-out lead is a decision, not an input.

Defers to: `docs/spec/07-decisions.md` (D34).

### `corpus attach`
**In** observations from `ig-intake --observations` (or a research file) and the
Leads of a *different* list. **Out** the same observations re-keyed onto that
list's `fetch.lead_key`. **Guarantees** a handle match is tried before a name
match, and that **an ambiguous match attaches nothing** — putting one coach's
posts on another produces a hook that is verified, quotable and about a
stranger. **Exit 1** when `--expect` is not met. **Exit 2** if either file
cannot be read.

### `triage`
**In** Leads, optionally their observations. **Out** a tier per lead — RUN,
HOLD or DROP — each carrying all three floor verdicts and the source that
settled them. **Guarantees** the floors are `qualify`'s, called rather than
re-implemented, and that **`unclear` is HOLD and never DROP**. **Never exits 1
on a routing decision**: a triage is a description, the same as a plan is, and
the operator reading the DROP list is the gate.

**`--complete-corpus` is the only thing that lets a stale date drop a lead**, and
it is an assertion the caller makes about the evidence, not a preference. See
D31.

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
the plan is printed and nothing is spent.

**A failed escalation is retried with `--escalate-only`, not with `--escalate`
again.** `--escalate` re-reads every site at tier 0 first, so the retry after a
403 on `2026-08-01-q1` read all 20 a second time and put 52 duplicate
`(lead, url)` pairs into the ledger — 52 of the 83 that batch recorded, in the
one batch whose purpose was a duplicate count. D22 states the risk in those
words and it happened anyway, because avoiding it meant calling `fetch.run_plan`
by hand and the CLI offered no narrower path. `--escalate-only` takes the saved
`sites.json`, runs the plans in it and reads nothing. **A retry must not be able
to pollute the measurement it is retrying.** Two vetted actors sit behind it, one
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
**In** the identities from `resolve --out`, optionally the Leads, which are the
only place a lead's own site URL lives, and optionally the address verdicts from
`email-find --out`. **Out** one `LeadPlan` per lead: the rungs that are populated
for that person, what each would cost, and which paid ones would be declined.
**Guarantees** every lead gets a plan, including a lead with no rung at all and a
lead whose every paid rung would be declined; it fetches nothing and runs no
actor. **Exit 2** if the identity file cannot be read, **exit 1** only if its own
output fails its own schema. Owned by `outbound/plan.py`.

**There are two decline rules and the second is the expensive one.** Ownership
declines a paid rung pointing at somebody else's channel, which saves a scrape.
`--addresses` declines every paid rung for a lead nothing can be sent to, which
saves the research, hook, verify and draft passes behind that scrape — and those
passes are the batch's actual bill. Both gate spend and never inclusion; both
leave the lead researched, planned, and holding a row.

**The ladder is here rather than in prose, and that is D23.** Where a hook comes
from was two markdown files kept in agreement by hand, and the agreement failed
twice on record. `LADDER` is now the authority; `docs/hook-rules.md` keeps what a
hook is and names this module.

**LinkedIn is two rungs.** A profile scrape and a posts scrape are different
actors at different prices — one batches its whole slice into a single container
boot and the other provably cannot — and they yield different kinds. While they
were one rung, a lead's plan named one price for a channel this machine buys
twice, and `metrics.rung_of` attributed three profile-sourced hooks to the posts
rung in the very number that settles F5. The rungs carry the URL shapes that
tell them apart, so attribution is derived and never reported; a LinkedIn URL
matching neither is named `linkedin_unattributed` rather than assigned, because
falling back to the first rung would re-create the conflation quietly.

**It declines, and the decline binds** (2026-08-01, D27). A step whose channel
is `absent` is labelled `decline`, and `hook-worker` may not escalate onto one.
Nothing in `plan` executes anything, so the enforcement lives in the consumer;
the reason lives here.

**It shipped advisory for two batches on purpose**, because a gate shipped
alongside its own measurement generates the data judging it. That objection was
paid off rather than dropped: `metrics --plan` now reports, of the leads
carrying a declined rung, how many produced a verified hook and how many
produced none — D21's reversal condition in D21's own words, finally computable.

**A decline gates spend and never inclusion**, which is the half that does not
change. A lead whose only paid rung is declined gets a null hook, a row and a
Blocker, never a drop. `plan` still exits 0 when every rung on the batch is
declined, because exit 1 there would turn an ownership verdict into the
inclusion gate D21 forbids.

`unknown` is never declined: it means no tell was available, not that the tell
said no.

**Pricing is opt-in.** `--price` needs a token and the network. Without it a paid
step reports "not priced", which is a different answer from an estimate of zero
and a different answer again from the cost gate's own "cannot be priced" — and a
batch nobody looked at must never report as a free one.

### `qualify`
**In** a research object, including the `observations` behind it. **Out** three
verdicts with their evidence, plus the captured fields. **Guarantees** `unclear`
passes and only a clear `no` drops a row. **Exit 1** on a clear `no`. **Exit 2**
if the input is not an object or a date will not parse. Owned by
`docs/spec/02-icp.md`.

**The activity floor settles from the observations, and only upward.** The
newest `published_at` inside the window makes it a `yes`, and **a `third_party`
observation is skipped**: somebody else's post about them is not evidence they
did anything, which is ban #7 one stage over and the rule `select` already
applies. Found on the first batch that ran this — a lead's only dated
observation was a company post naming her, two days old, and the floor called
her active on it. Dropping an observation only ever removes evidence, so it can
move a lead toward `unclear` and never toward a kill. Outside the window it
settles nothing: a lead whose observations are all stale comes back exactly as a
lead with no observations does, and falls through to the page-text rung
unchanged. That restriction lives in `activity_from_observations` rather than in
a caller's discipline, because `check_active` answers `no` to a stale date — so
passing one through would open a new kill surface at the one floor built not to
have one, on the weakest evidence there is: that the pages we happened to
retrieve were old. Better evidence is a reason to settle a floor, not a reason
to weaken `unclear` passes.

Until 2026-08-01 the floor had no evidence at all. A coach's own website almost
never carries a date — zero usable ones across nine sites and about 220,000
characters — so every lead read `unclear` and the floor did nothing, and the
repair was a write-back from the hook stage that an orchestrator had to
remember. The dates existed one line earlier: research workers have returned
schema-checked observations since the contract landed.

**Two routes reach the activity floor and both are upward-only.** A stale date
returns `unclear`, never `no` — from a list of observations, and from a research
object's own `last_activity` field, which had no such guard and killed 9 of 62
leads on `2026-08-03-icf1`. Their workers had recorded `active_recent: unclear`
beside the real older date they found, and the floor overrode that verdict with
a harsher one derived from the same evidence. `--complete-corpus` is the only
thing that re-opens the kill, and it is an assertion about the evidence rather
than a preference. See D31.

### `research`
**In** a worker's returned object, or an array of them. **Out** a schema verdict.
**Guarantees** a verdict outside the enum is caught, and **a hard yes or no with
no source named is rejected** — that combination means the answer was reasoned
rather than fetched. This is the stage with no verifier agent on purpose: a
schema check is cheaper than an agent and strictly harder to talk around.

The object may also carry the observations behind those verdicts, and they are
validated here through the same call — capped, so one worker that got an enum
wrong cannot bury the floor violation that actually drops a row. See `observe`.

**A clean lead reports as one line.** The full block is four lines of evidence
that only matter when something is wrong, and the orchestrator runs this once
per slice *and* again on the merged file — 14,202 bytes on a 28-lead batch,
against 2,316 in the headline form, every byte of it resident for the rest of
the run. The blockers stay on the line, because they are the part that gets
read. `--verbose` restores the full block, and one lead is always full.
**A blocker is not what triggers the block**: this gate runs before the hook
stage, so every lead is blocked on `no hook` at the moment it is validated.
Only a schema problem is loud.

**This is the machine's retrieval stage as of D27**, which is a change in what
the objects are *for* rather than in what validates them. Nothing downstream
fetches for a hook: `select` ranks what research returned and `hook-worker`
quotes it. **An observation a worker does not return is a hook nobody can
find**, and it will present as the lead's fault rather than the retrieval's. The
podcast search moved here for the same reason — it was `hook-worker`'s free
rung, it reaches the coaches who do not post, and removing that agent's
`WebSearch` would otherwise have deleted it silently.

### hook
Two agents **and** a command. `hook-worker` chooses from `select`'s shortlist,
quotes it verbatim and writes the clause that says what it took; `hook-verifier`
re-fetches the citation in a context that never saw that choice and defaults to
refuted. **Three verdicts, not two** — INCONCLUSIVE holds the lead where it is
rather than killing it. **No hook found is a good answer**: the lead holds and
gets no row, and post-flip it is explicitly the cheaper answer than an
escalation. `docs/hook-rules.md` owns the rest.

**The worker does not search** (D27). It has no `WebSearch`; it keeps `WebFetch`
for one bounded escalation against a URL `plan` already named, which may not be
a rung `plan` declined. Every retrieval left at this stage is one somebody can
see and price.

**In** a proposal, or a list of them. **Out** a pass or the list of what has to
change. **Guarantees** it fetches nothing, rewrites nothing, and never touches
the quote. **Exit 2** if the input is not proposals, **exit 1** on any finding.
Owned by `outbound/hook.py`.

This closes **F4**: the hook was the only consequential artifact with no
mechanical gate, while research and observations both had one. The cost was
measured — six of twelve drafts on `2026-08-01-q1` had to alter text a verifier
had certified word for word, over an em-dash, spaced hyphens, "touchpoints" and
four figures. Every one of those is a rule the linter has always held and the
hook stage never ran.

**The ordering is the whole point, and it is F11's shape again.** When a quote
breaks a voice rule the honest repair is to pick a *different* quote, and only
the worker can do that: it has the page open and the verifier has not run. One
stage on, the drafter has neither the alternatives nor the authority, so it
edits the citation — and a hook squeezed after certification is a citation
drifting from its source. So every finding names the quote as the thing to
change and nothing here ever offers a repaired string.

It also refuses a **structurally uncitable URL**: a LinkedIn post link with an
empty slug (`/posts/<name>_-activity-…`) is what harvestapi builds when a post
has no text to name it, and it 404s. The content can be real, paid for, and
still impossible to cite — that failure cost a lead and a full verifier pass to
discover.

**The date comes from the cited observation, not from the writer.** An undated
evergreen source (an About page, a framework) takes an empty `published_at`, and
a non-empty one on such a source is **rejected as fabricated**. Requiring a date
from a page that has none is what produced two invented dates on
`2026-08-02-q2`. Where the gate cannot see the source — no `--against`, or a
declared escalation — the old rule stands and a date is required, because an
unjoinable claim of "the page had no date" is indistinguishable from not looking.

**`--against work/select.json` checks the quote against the observation it
names**, and that closes ban #3 — *"no invented specifics"* — which was a
sentence an agent was asked to remember for as long as there was nothing to
check it against. The quote must be a contiguous piece of that candidate's
stored text, compared on normalised whitespace only: a scraped post carries line
breaks a quote will not, but a changed word is the exact drift the check exists
to catch, so case and punctuation are not forgiven. It also catches two
sentences welded together, which is a real refusal from `2026-08-01-q1`.

**A blank `observation_id` now means one of two opposite things**, so it has to
be declared. Before the flip it was ordinary — the hook stage did its own
fetching and most hooks had no stored observation behind them. Now it is either
a bounded escalation the worker walked and named, or a hook composed from
nothing, and only the worker can say which. `escalated` with an
`escalation_rung` is legal; neither is a failure. Declaring both an escalation
and an `observation_id` is a contradiction and is refused.

Without `--against` the join is not checked and the report **says so on that
run**, because a PASS that checked less has to be tellable from one that checked
more. The single-lead repair path in `outbound-draft` has no batch behind it and
uses that.

**A pass is still not verification.** Nothing here has looked at the page.

### `select`
**In** research objects, which after the hook stage carry both halves — the
observations the research workers kept, and the hook fields the hook stage wrote
back. **Out** one `LeadSelection` per lead: a ranked shortlist of three
candidates and the ban that excluded everything else. **Guarantees** it fetches
nothing, writes no hook, and never changes which lead is drafted; every lead gets
a selection, including one with no observations. **Exit 2** if the input is not
research objects, **exit 1** only if its own output fails its own schema — a
disagreement is never a failure. Owned by `outbound/select.py`.

**It runs before the hook stage and the hook stage consumes it** (D27). Each
lead gets up to three candidates carrying their observations' stored text;
`hook-worker` picks one, quotes it and writes the clause. Three, so that a
rejected first pick needs no second retrieval — the shortlist is sized to make
the escalation rare, not to offer a menu.

**`--against` survives with its verdicts re-read.** It compared the ranker's
pick to a hook the stage had already paid to find; now the hook comes from the
shortlist, so the same five words say what the worker did with it. `agreed` is
rank 1, `shortlisted` is rank 2 or 3, `missed` is a ban to re-examine, `no_pool`
is a fact about the corpus — and **`unobserved` is the escalation rate**, which
is the number D27 is judged on.

**Four of the twelve bans stop being something an agent must remember** —
third-party coverage, stale news, generic site copy, and invented specifics,
the last through the `obs_id` join. `docs/hook-rules.md` still owns all twelve.

**Generic site copy is repeated text, not an About page.** `2026-08-01-q1`
MISSED three leads and all three were `kind: about` observations a verifier had
independently confirmed; that one ban was 21 of the corpus's 32 rejections. What
the verifier refuses is the generic, and the only mechanical form of that is the
same text appearing for two different leads. An About page now ranks last and is
offered when the lead has nothing better.

**`--batch` writes the corpus as well as the verdict**, into `data/runs/`. Only
the verdict was kept for `2026-08-01-q1` and the input lived in `work/`, so the
batch that disproved a ban could not be re-scored against the fix. Both files
are committed; `select data/runs/<batch>-research.json --against` re-runs the
measurement for free after any change to the bans or the ranking.

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

`deal` runs on the draftable set, before the hook stage, and prints the
`HOOK ROOM` the hook stage and `select --hook-room` are then given. **That
figure is a floor, not an estimate** (2026-08-02): the drafter authors the
identity beat, so a room computed against the reference identity line is only
true if that sentence comes out reference length, and drafters write to the top
of a range. `Deal.authored_budget()` is the exact joint budget for hook and
identity together and is the only length figure true at deal time;
`Deal.hook_room()` subtracts the top of the identity range from it so the number
holds however the beat is written. `_resolve_length` repairs against the same
floor, because a promise the allocator does not honour is not a promise. **Its cost
is that lines are allocated to leads that later hold on a refuted hook**, so the
shipped batch drifts from the declared weights. `export --rebalance-ps` is the
existing mitigation and now fires on most batches rather than some; re-dealing
is not the answer, because the drafts and the CRM rows are written against the
file this produced.

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

**Two checks that only a batch or a beat pair can see.** A four-word phrase
shared by two hooks is a template — the hook is the beat that proves per-lead
authorship, and "Most people [verb]" was the writer's clause in two drafts on
`2026-08-01-q1`, each fine alone. And a close that opens on a question invites
"no", which is the one thing an ask may not be. Both are **warnings**: nobody
has measured how often an innocent four-gram recurs, the close is bank copy
whose fix is one edit in Airtable, and a gate that halts a send file over an
editorial judgement is one people learn to route around. `copy-check` reports
the close at the source, on a passing run as well as a failing one.

**Quoting is not claiming.** A figure that is in the hook beat *and* in the
certified `hook_quote` is the recipient's own fact and is exempt. Without that,
the rule written to stop us relabelling a client result was instead deleting
"70.3", "2023" and "27 years" out of the one beat whose job is to prove we read
their page — six of twelve drafts in `2026-08-01-q1` had to alter a hook a
verifier had certified word for word, and both drafters kept the digits by
moving them into the subject line, which nothing checks. The exemption is the
**intersection** of the two texts, applied to the hook beat's own words rather
than to a value, so a figure the drafter introduced is still caught and nothing
leaks into the identity beat. A hook carrying a figure with no quote passed is a
warning, never a silent pass.

### `export`
**In** drafts. **Out** `out/leads.csv`, `out/preview.txt`, `out/shipped.json`,
`out/wall-additions.csv`, `out/line-usage.csv`, `out/rejected.txt`.
**Guarantees** an email that failed the lint is *absent* from the upload file,
not flagged in it; and that all six outputs are cleared first, so a blocked
batch cannot leave a stale uploadable file behind.

**`shipped.json` is the drafts exactly as they entered `leads.csv`, and it is
what `crm-rows --drafts` must read.** `--rebalance-ps` swaps a ps line in this
command's own memory and never writes it back, so the working drafts file keeps
the old one — on `2026-08-03-ig237` the CRM said `ps=ps-04` while the reader got
`ps-05`. Same rule as `Hook`: the row says what the reader saw. `--anchors` additionally
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

### `crm-rows`
**In** the normalized Leads, the research objects, and optionally the drafts
that shipped. **Out** `out/crm-leads.json`, one Airtable Leads row per
researched lead. **Guarantees** the join is explicit and fails closed, every
field is written including the empty ones, and coverage is reported for every
field rather than the ones anybody expects. **Exit 2** if an input is not an
array, **exit 1** on any problem. Owned by `outbound/crm.py`.

**It writes nothing to the CRM.** `audit/airtable.py`'s boundary is that a Lead
row lands where a human sees it, and that stays — this computes, a person
performs the write. What was wrong on `2026-08-01-q1` was never that a model did
the typing; it was that a model did the *join*, from memory, in a script nothing
tested.

Twenty rows went in with **no First Name, Last Name, Website, LinkedIn or City
on any of them**, built from `work/researched.json` — which has never carried
the intake identity fields, because those live on the normalized Lead. A filter
dropped every empty key before the request, so there was no error and no
warning. A research object with no lead behind it is now a failure naming the
columns that would have gone in blank.

**Coverage is the other half, and it answers the check that missed it.** The
verification that passed those rows counted Name, Status, Hook Verified and
Blockers — four fields somebody expected to be populated — and reported 20/20. A
check that only looks where you expect to find something is the writer
certifying its own work with extra steps. So every field is counted and a field
empty on every row is named, because "nobody has a City" and "the City never got
read" print identically otherwise, and the report says a zero is not
automatically wrong rather than implying a verdict.

**Required is `Name`, `Email`, `Status` and nothing else.** Everything else is
legitimately absent for some real lead. A longer list fails closed on true rows,
which teaches people to pass a flag that turns the check off.

**`Batch` is deliberately not in a row.** It is a linked-record field whose
value is a Batches record id that does not exist until that row is created, so
the label is reported instead.

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

### `email-find`
An address **somebody else published**, in one batched search run. The third
and last address path: `extract` harvests what is printed on the lead's own
pages, `email-enrich` guesses at their own domain, and both only ever look at
the lead. A coach's address is routinely printed by an accreditation body, a
directory, or a company page and nowhere else, which is why on the probe that
justified this stage four of five addresses were found off-site and two were on
domains the machine had never seen.

**`--observations` harvests before it searches, and that half is free.** An
address the lead printed in their own bio is better corroborated than anything
this stage can buy — it cannot be a different person of the same name, which is
this stage's own failure mode. A lead with one is not searched at all, so the
harvest saves the query as well as finding the address. Measured on
`2026-08-03-ig237`: the SERP found 6 addresses across 23 leads, and **2 of the 4
that survived corroboration were not among them** — they were in bio text the
dump already carried and no stage read. It is still a candidate a human
confirms, and it still goes to the verifier.

**An organic result is a citation; an AI Overview is a claim**, and the verdicts
keep them apart. `FOUND` carries a URL that can be re-fetched, which is the
standard `hook-verifier` already holds a quote to. `CLAIMED` means only the
overview said so — it must be confirmed on its cited page or dropped, never
adopted, because on the probe it produced a plausible role address on a real
domain, attributed to a real page, for a mailbox that does not exist. Nothing
here adopts anything either way: every candidate still goes through
`email-check` and `email-verify`, which is what turned that fabrication into a
hard FAIL instead of a send.

**An address needs a reason to be believed this lead's**: their name in the
local part, a domain already known to be theirs, or a source page that names
them in full. Without that rule the first live run reported `FOUND` four times
in five on strangers' addresses, because a query about a person returns pages
that merely mention them and each carried exactly one address, which ranking
floated to the top. Uncorroborated addresses are counted in the report and kept
out of the candidate list — a dropped address stays visible, since the filter is
a heuristic and the count is how anybody notices it going wrong.

**The query carries the lead's known domain**, and that one term is the
difference between a run that finds four addresses and a run that finds none. A
coach's address is indexed beside their business name far more often than beside
their positioning line. A link-in-bio or storefront host is never used as that
term — searching `whop.com` searches for Whop.

**The AI Overview is off by default, and it was on for one commit.** It nearly
doubles the per-query price — `audit/apify.py` owns the event prices and the
ledger records what a run actually cost — for an `ABSENT` verdict that
measurement did not support: it was wrong on two of five leads whose addresses
were live on their own homepages at the time. `--ai-overview` turns it on for a
lead where an absence is the actual question. Do not pay for it five hundred
times.

`ABSENT` still means what it says — the overview stated no public address
exists — and it requires both a stated absence and no organic candidate, so a
model hedging in prose loses to the SERP underneath it. `NONE` is the different
answer where nothing was found and nothing was said, and collapsing the two
would make an unanswered query look like a confirmed dead end. **Neither verdict
is what `plan` declines on**; see below.

**`--out` writes the per-lead verdicts, and `plan --addresses` reads them.**
That join is the point of running this stage early. A lead marked
`reachable: false` — no address on the row, none harvested from their site, none
published anywhere searched — loses every **paid** rung and keeps every free one.

It is a measurement and never a prediction: `reachable` is false only when every
cheap path has already looked, never because the AI Overview offered an opinion.
And it gates spend, never inclusion, the same asymmetry the ownership decline
holds. The lead is still researched, still planned, still gets a row.

**This decline is worth far more than the ownership one.** A hook costs one
scrape and several agent passes, and the passes dominate by orders of magnitude
— `2026-08-02`'s token forensics measured the ratio, `docs/journal.md` records
it, and `usage` and `ledger` are the two commands that report the halves. A lead
nothing can be sent to that still walks research, hook, verify and draft spends
all of that on an email nobody receives.

`ABSENT` exits 0 alongside `FOUND`: a null result reached honestly has always
been a good answer here. `CLAIMED` and `NONE` exit 1 as open work, and a search
layer that could not run exits 2 — the `email-verify-batch` rule again, since a
dead fetch layer must never read as "these leads have no address".

The logic lives in `audit/email_find.py` and **fetches nothing**, the same
property that made `audit/footprint.py`'s retirement a deletion rather than a
rewrite. `audit/apify.py` owns the fetch and which actor `serp` names.

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

**A SERP actor came back 2026-08-03 as `serp`, for a different job.** The
retirement above was about **sourcing**, where the free path still does the work
and nothing has been restored. `email-find` is **address retrieval**, which was
not a stage then, and the probe that added it measured why free search cannot
serve it: the agent's WebSearch is US-geo'd with no country control, returns a
summariser's paraphrase rather than the results, and answered three of five
UAE-coach queries with the wrong person. `countryCode` and raw organic results
are the difference. It is priced per event rather than per compute-second, so
batching saves the one-off start fee and nothing more — still worth doing, but
without the container-boot economics that make batching dominate everywhere
else here.

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

**The payload goes to a file; stdout gets a summary.** Every other bulk stage
here does this — `fetch`, `select`, `plan`, `metrics`, `export`, `crm-rows` —
and `apify` was the one that did not, printing its whole dataset into the
caller's context by design. On `2026-08-02-q2` three Instagram runs produced
914,685 bytes of tool-result, roughly 305 KB each where a trimmed result is
20-30 KB, and its token forensics could not account for them at all. The summary
names the item count, how many carry text and the date range, which is what
decides whether the file is worth opening. `--print` restores the old behaviour
for debugging by hand. `limits` and `actors` still print: their output is the
answer, not a payload.

**The field trimming recurses.** `_lean`'s allow-list branch used to copy nested
records through verbatim, so `latestPosts` on a profile and `author` on a post
each carried the media blobs the trimming exists to drop — a leaned profile
shipping a dozen unleaned posts inside itself. `--raw` still bypasses trimming
entirely, and is harmless now that raw goes to disk.

### `observe`
**In** one observation, an array of them, **or a research file, which it
unwraps**. **Out** the schema verdict.
**Guarantees** a record claiming to be something fetched can be checked when it
is written: platform, kind and author inside their enums, a piece of content
carrying its text, a publication date that parses and has already happened, and
a `retrieved_by` naming a rung this machine actually has. **Exit 1** on a
violation, **exit 2** if the input is not an object or an array of them. Owned
by `outbound/observe.py`.

**One stage consumes it: `qualify`'s activity floor.** The newest
`published_at` settles `active_recent`, which is the first dated evidence that
floor has ever had. Nothing else reads observations — the hook stage still does
its own fetching, and the duplicate that makes unnecessary is left in place on
purpose so `ledger report` can price it.

**The point is what research does not do.** Research keeps a `_source` string
per verdict, so the post that settled `active_recent` — the exact material a
hook is made of — was read once, reduced to a boolean, discarded, and paid for
again one stage later. The floor is the first half of that undone: the boolean
now comes from a record that kept the post.

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

**The flip's own two numbers** (D27). `escalation_rate` is the share of hooks
carrying no `observation_id` — ones the shortlist did not hold and the worker
went and fetched. Rising means selection is not reaching the material, and the
fix that points at is research fetching deeper rather than a change to the
ranker. It counts every attempt, not only the verified ones: an escalation that
produced a refuted hook still cost the fetch the flip was meant to remove.

`declined_and_dry` needs `--plan` and is **D21's reversal condition in D21's own
words** — of the leads carrying a declined rung, how many produced no verified
hook, against how many did. Declining is free where those are the same leads and
wrong where they are not. Without a plan file it prints `?`, because a `0` there
would read as "declining cost nothing", which is the claim being tested. A
declined lead that never reached the hook stage is skipped rather than counted
dry: it says nothing either way, and counting it would charge the gate for a
lead the floors dropped.

**`ledger pass` is the Claude bill, and nothing here could see it.** This module
exists because every claim about what *retrieval* cost had been reconstructed by
hand from a journal entry. The model side was in exactly that state one layer
up: `2026-08-01-q1` cost about 64 agent passes for 20 leads and 5 shipped rows,
and the only record was a single number an orchestrator typed into `metrics
--passes` at the end of a long session. No stage, no model. "The drafting loop
is most of the bill" was a guess nobody could check.

`ledger pass --stage <s> --agent <a> --model <m> [--count n]` writes to the same
file with `kind: pass`, so a pass can never be counted as a fetch, and `metrics`
prints `passes_by_stage` and `passes_by_model` labelled **REPORTED, not
measured** — the same trust `ledger add` carries and for the same reason: an
agent pass happens in the main loop and Python cannot see one. Nothing reported
prints `?`, never `0`; a zero would read as "this batch used no agents".

**Counts, not dollars.** Model prices are a value this repo does not own, and
the standing rule is that a doc names its authority rather than copying it. A
rate table here would go stale in a file nobody remembers to update and print
with two decimal places while doing it.

**`ledger batch` makes the label discoverable rather than remembered.** With a
label it writes `work/BATCH`; with no argument it prints the label that resolves
now and where it came from. The order is the argument, this process's context,
`OUTBOUND_BATCH`, `work/BATCH`, then today. On `2026-08-01-q1` twelve workers
were told to pass a `--batch` flag that did not exist, and `OUTBOUND_BATCH` is a
shell variable a subagent does not inherit — so 15 retrievals, five of them paid
hook rungs, were billed to a file named after the date and `ledger report`
under-reported the batch by 30%. Every `apify` subcommand now takes `--batch`
too, and neither is something a worker has to be told. **An unnamed batch is
never an error**: the label falls back to the date and the report says which
happened, because dropping a paid fetch's accounting for want of a label is
worse than filing it under the wrong name.

**Reporting a duplicate is the job; failing on one is not.** A gate that can
halt a real send file over an accounting line is a gate people learn to route
around — the same reason `doc-check` runs with the tests rather than with a
batch. The stage that removes the duplicate is the one that gets to block on it.

**`report` groups duplicates by shape, because the shape is the finding.**
`2026-08-02-q3` produced 129 duplicate pairs and its journal entry names the
answer in one sentence — 110 of them were a single shape — reached by reading
129 lines that differed only by a name, all of which stayed in the
orchestrator's context afterwards. Grouped, that batch reports in 1,474 bytes
where it used to take 15,905, and the dominant shape is the first line rather
than an inference. `--verbose` prints every pair.

**The costs are estimates, and the ledger says so.** The runner uses Apify's
run-sync-get-dataset-items, which collapses a run to its output, so the billed
`usageTotalUsd` on the run object is never fetched. A ledger implying otherwise
would be worse than none.

### `metrics`
**In** the batch's research objects, plus the counts earlier stages printed.
**Out** what the hook stage yielded and what the leads that yielded nothing
cost, and the Batches row as a paste-ready block. **Guarantees** a count nobody
supplied prints `?` rather than `0`. **Exit 2** on a ledger it could not read.
**Never exit 1.** Owned by `outbound/metrics.py`.

**`?` is not zero, and that is the whole design.** The dedupe wall's asymmetry
and the ledger's, a third time: a missing wall must never read as "nobody has
been contacted", a missing ledger must never read as "this batch cost nothing",
and an unsupplied raw count must never read as "no leads came in". A zero is a
measurement. A metrics block that quietly zero-fills is worse than no block,
because it looks like evidence. The cost field is the sharpest case — a zero
cost from an unopened ledger and a zero cost from a genuinely free batch are the
same number and opposite facts, so the first prints `?` and only the second
prints the figure.

**`yield_by_rung` is the number that settles F5**, which says the cheapest rung
produces the observations most likely to be refuted. The rung is derived from
the hook's source URL rather than reported, so a worker cannot mislabel the
number judging its own rung. `plan.LADDER` owns the rungs and
`normalize.classify_site` owns the platforms; neither is restated (D23).

**`wasted_retrieval` is what the retrieve-once work is trying to move** — paid
fetches on leads that produced no verified hook. Free rungs are excluded, since
the figure's use is deciding whether a *purchase* was worth making, and a
verification fetch is excluded because it is spent on a hook that exists.

**It prints the Batches row and does not write it.** `audit/airtable.py` states
the boundary — writes stay narrow, a row lands where a human sees it — and a
metrics command is not the place to widen it. What was wrong was never that a
model did the typing; it was that a model did the arithmetic, from memory, at
the end of a long run.

`agent_passes` is **reported on trust** and labelled so. Python cannot see an
agent pass, the same blind spot that makes a worker's own WebSearch invisible to
the ledger, and `ledger add`'s answer applies here too: record it, keep it
distinguishable from what was measured.

**`tokens` is the same bill, MEASURED**, read from `<batch>-usage.json` and
printed apart from the reported block so the two authorities never share a line.
`tokens_per_email` divides by `written`, which is `?` until a stage supplies it.

### `verdict`
**In** one cold read, a list of them, or a `{slug: verdict}` map. **Out** the
schema verdict. **Guarantees** a REWRITE naming no problem is rejected, and
`beat` is an enum. **Exit 2** on an empty wave. Owned by `outbound/verdict.py`.

**The draft verdict had no artifact until now.** `draft-verifier` returned SEND,
REWRITE or REJECT as prose and had no `Write` tool, so this spec's own line was
that the verdict lives in an agent and nothing in Python can reach it. `REWRITE`
appeared in zero Python. A verdict only the orchestrator can read is a verdict
only the orchestrator can route, which is why every one arrived on its own turn
inside a context that reached 578k-684k tokens.

The shape is `draft-verifier.md`'s own contract — `verdict / seam / voice /
problems[{beat, sentence, problem}]` — with one change: the last key was written
in English and is now an identifier, because a field that gets counted needs a
name. **`beat` is an enum for the same reason.** "the identity line" and
"identity beat" would be two buckets and a wave of seventeen identical findings
would report as seventeen one-of-a-kind problems, which is the state this exists
to fix.

**A REWRITE with no problems is rejected**: the drafter would be re-run against
no instruction, a full opus pass that cannot improve on anything.

### `redraft`
**In** a directory of `verdict-<slug>.json`, or one file holding them. **Out**
who is redrafted, who holds, and one shared note per beat a wave failed on.
**Guarantees** the round cap is a loop bound. **Exit 2** on a malformed verdict.
**Never exit 1** on a routing decision. Owned by `outbound/redraft.py`.

**The cap was always specified and it lost twice.** "Back to the drafter once,
then it either passes or it holds" is in the batch skill and has been since it
was written. Eight of nine leads exceeded it on `2026-08-02-q2`, one running five
rounds; eight leads exceeded it on `2026-08-02-q3`, three running three. The
repeats were 68% and 46% of those draft stages. A long session talks itself past
a sentence one reasonable exception at a time and cannot talk itself past a loop
bound.

**The clustering is the larger half.** Seventeen of seventeen q3 drafts failed
their first cold read on the same beat and were answered individually — nineteen
redraft prompts carrying 1.6x the text of all seventeen original briefs. Nobody
was careless: a reader going lead by lead cannot see the seventeenth until they
have paid for sixteen. When a beat accounts for at least `CLUSTER_MIN` of a
wave's rewrites, this says so and emits **one** correction naming the beat and
the leads. Below that threshold it says the problems are genuinely separate, and
separate notes are right.

**It routes; it does not draft**, the same boundary `crm-rows` keeps.

### `collect`
**In** a directory of per-lead files. **Out** the stage's state file, plus
coverage. **Guarantees** a missing expected member, an unreadable file, or an
empty stage all fail closed. **Exit 1** on any of those. Owned by
`outbound/collect.py`.

**Three files here were written by no command**: `work/researched.json`,
`work/draftable.json`, `work/drafts.json`. The orchestrator serialised each out
of its own context — the parts already in a 600k-token window, the whole emitted
as output, then read back as a tool result. It also made every stage
unresumable, since a file that exists only because somebody remembered to write
it cannot be picked up by anything that was not there.

**`--expect` is the check.** `crm-rows` is the precedent: twenty rows once went
in with no First Name, Last Name, Website, LinkedIn or City on any of them, and
the check that passed them looked at four populated fields and reported 20/20. A
count of what was found is not a count of what should exist.

### `brief`
**In** the run's `work/` and `out/` directories. **Out** how far the run got,
each count for the final brief with the file that proved it, the next command,
and — with `--metrics-command` — the `metrics` call this run has earned.
**Guarantees** a count no file proves prints `?` and is left off the generated
command line; an unknown `--note` key is refused rather than stored. **Exit 2**
when `work/` cannot be read or a note is malformed. **Never exit 1.** Owned by
`outbound/brief.py`.

**This is what makes a stage boundary a place to stop.** A batch ran as one
session because nothing could tell a fresh one where it had got to, and that
session's own context is the largest line item in the machine: 166.5M of icf1's
261.0M tokens, 79.6% of the Opus bucket, against 40M for both Opus agents
combined. `cache_read` is the sum of the context over every turn, so the growth
from 30k to 600k is paid for hundreds of times. Six short sessions cost a
fraction of one long one and change no gate, no verifier and no tier.

**Almost all the state was already on disk.** What was not was the residue of
counts each stage printed and nothing kept — every flag `metrics` takes. Those
reached `metrics` by being retyped at the end of a long run, which is the exact
habit the `?`-not-`0` rule exists against, performed by the reader the rule was
written for.

**It derives and it does not infer.** `warm` is the case that defines the line:
`dedupe` exits 1 on a warm hit and stops the run, so a `clear.json` on disk
implies nobody was warm. That inference is available, correct almost always, and
refused — it prints `?` and takes a note. The five note keys are closed
(`source-list`, `warm`, `copy`, `apify-budget`, `chunk`); a free-form note file
would be a second state store with no schema, which is the shape of the problem
this command removes.

**Fails open, like `ledger` and `metrics`.** An observer that can halt a send
file over an accounting line is one people learn to route around.

### `usage`
**In** the session's own transcripts. **Out** what the batch cost in agent
tokens — totals by bucket and model, the orchestrator/subagent split, a
per-agent-type breakdown, and **what the orchestrator's context is made of** —
plus `data/runs/<batch>-usage.json`. **Guarantees** a transcript it cannot parse
is an error naming where it looked, never a zero. **Exit 2** on that. **Never
exit 1.** Owned by `outbound/usage.py`.

Claude Code discovery uses the project directory under `~/.claude/projects`.
Codex discovery reads rollouts under `~/.codex/sessions`, restricts them to this
repository, and when `work/BATCH` exists includes sessions written since that
marker so `/clear` stage boundaries remain cumulative. `--transcripts` accepts
an explicit file or directory for either host.

**Totals say a batch was expensive; the block profile says what to stop putting
in the loop.** `cache_read` is the sum of the context over every turn, so it
falls with a smaller context *and* with fewer turns, and rises quadratically when
a run gets both longer and chattier. The profile splits that context into
thinking, tool results, the model's own tool calls, and prose — and the split is
why it exists. The rule it replaced reasoned from the true observation that
two-thirds of the re-read is the orchestrator's own writing and concluded "never
narrate per lead"; measured, prose to the operator is the smallest of the four
and thinking is the largest. A fix aimed at the wrong quarter is the thing this
number prevents.

It counts characters rather than tokens and says so: the transcript records no
per-block token count, and a tokeniser here would be a second estimate dressed
as a measurement. It profiles the main thread only — a subagent's context dies
with the subagent and is already reported per agent. A profile of nothing prints
no section at all rather than a row of zeroes, which is `metrics`' rule about a
count nobody supplied.

**A pass count is not a magnitude.** `ledger pass` records that an agent ran,
because neither an orchestrator nor a worker can see its own token usage. So the
model side had a count and nothing else: `2026-08-02-q2` reported 99 passes and
`2026-08-02-q3` reported 185, both true, and neither could say that the two
batches spent about 410M tokens to ship 22 emails.

**The orchestrator is the largest stage and reports no passes at all**, because
nobody records a pass for the loop they are typing in. Measured, it was 75% of
both batches — one thread whose context reached 578k-684k tokens, re-read on
every one of ~390 turns. That is the line `ledger pass` cannot express and the
reason this command reads transcripts rather than asking.

**Tokens are the measurement; dollars are derived and carry an expiry.** A token
count is a measurement this repo owns and it never goes stale. A price is not,
which is why `ledger pass` refuses a rate table — "a number going stale in a
file nobody remembers to update". That names the failure mode correctly and
draws the wrong conclusion: the danger is not that a price is written down, it
is that it goes wrong **silently**.

It already did. The two 2026-08-02 forensics runs priced Sonnet 5 differently —
one used the introductory rate, one used list — so the combined figure quoted
for days mixed two bases and was off by about 2%. Neither run was careless;
nothing told either one which rate applied.

So the rate card carries the date it was read, Sonnet 5's introductory rate
carries the date it expires, and **`price()` returns nothing once either has
passed** — the report prints tokens and says why it could not price them. A
model with no rate on file withholds the *whole* total rather than reporting one
that quietly omits part of the run. The cache tiers are priced apart, because a
1h write costs 2x base input against a 5m write's 1.25x and the orchestrator
writes at 1h while every subagent writes at 5m — that split alone was ~30% of
the measured bill. Every figure is labelled **equivalent list cost, not an
invoice**: this account bills on a subscription.

**Deduplicated on `requestId`, last record winning.** A streamed response emits
several records under one id with `output_tokens` growing across them. Counting
records inflates the request count 2-4x; keeping the first undercounts output by
about 4x. Both forensics runs found this independently and one of them found it
after publishing a wrong total.

**Transcripts die with the container**, so this runs before the session ends or
the batch's largest cost is unrecoverable. `--transcripts` points it elsewhere
when the harness moves the layout, which is why the layout is sniffed rather
than assumed — the same reason `replies` sniffs Smartlead's columns.

**It is checkpointed at every stage boundary, not run once at the end.** This is
the one way it differs from the retrieval ledger and the difference is a real
gap: the ledger appends a line at the moment of each fetch and is committed, so
a batch that dies in stage 3 still leaves its accounting. `usage` computes a
snapshot on demand and writes nothing until it is called, so a session that
closed early would leave no record of the largest cost in the run. Rewriting the
artifact at each boundary closes that. `--quiet` prints one line for those
calls, because eleven lines five times over is sixty lines of the orchestrator's
own context spent watching itself — a small version of the thing being measured.

### `replies`
**In** a Smartlead replies export and the batch's leads. **Out** reply rate
overall, by `hook_type`, and by the rung the hook came from. **Guarantees** a
column it could not identify is an error and never a zero reply rate. **Exit 2**
when it cannot read the file or name the columns. Owned by
`outbound/replies.py`.

**This is the one gap no retrieval architecture closes**, and it is a manual
bridge on purpose. Smartlead owns replies, there is no API key in this repo, and
`docs/spec/06-state.md` records that handover as a CSV. So Haytham exports and
this joins on `email`. It is what finally makes `Hook Type` testable against
reply rate — the CRM field's own description calls it *"a testable variable
against reply rate rather than a detail buried in prose"*, and the test has
never been run.

**The columns are sniffed because nothing here has ever seen a real export.** A
hard-coded name would fail on first contact, and fail silently if it happened to
match something else. An unfindable column names the headers it did see;
`--email-column` and `--replied-column` override the sniff.

**A pre-filtered export is never inferred.** A file where every row is a reply
and a file whose reply column went unrecognised look identical and differ by the
whole answer, so `--all-replied` says which, and without it the second is an
error. In a status column an unrecognised value counts as **not** a reply and is
named: under-counting understates a campaign, while over-counting makes a hook
type look good and drives a real decision on a word nobody checked. Ordinary
statuses (`SENT`, `OPENED`, `BOUNCED`) pass silently, so the note only fires on
something genuinely new.

**It draws no conclusion.** One batch is a handful of samples per bucket. The
report says so in a line, because a percentage over three leads reads as a
finding to anybody skimming.

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
