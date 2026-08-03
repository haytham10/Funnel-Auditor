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
ig-intake   an IG profile dump -> Leads AND the posts it already carries, which
            is the paid IG rung arriving with the list. A corpus, not a source
            list: attach it to a list that has addresses (D32)
icf-intake  an ICF directory export (.xlsx) -> Leads AND the ICP fields the
            coach filled in themselves. The values are cell hyperlinks, not text
channel-find the LinkedIn / Instagram / website a directory list arrives
            without. A URL needs a reason to be believed theirs, or the field
            stays blank
icf-export  the enrichment joined back onto the workbook, plus the committed
            CSV and leads.json
triage      RUN / HOLD / DROP before anything is spent. `unclear` is HOLD
dedupe      name/domain BEFORE any paid call; email again after research
fetch       free local HTTP first; ONE batched Apify run for what it can't read
resolve     which channels are plausibly theirs, typed and evidenced
plan        which hook rungs a lead has and what each costs. A decline BINDS
research    research-worker per slice -> typed objects AND the observations
            every later stage reads. This is the retrieval stage
deal        the four hand-written lines, allocated for the whole batch at once
select      rank the observations -> a shortlist of 3 per lead. No fetching
hook        hook-worker quotes the shortlist and writes the clause -> gated by
            `main.py hook --against` -> hook-verifier re-fetches the citation
draft       draft-worker writes against the anchors -> draft-verifier reads cold
lint        every check that can be mechanical, failing closed
export      leads.csv (8 Smartlead columns) + preview.txt + wall-additions
crm-rows    the Airtable Leads rows, joined explicitly. Python computes, a
            human writes
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
- **Never invent a channel**, which is the same rule one stage earlier and with
  worse consequences. A found LinkedIn or Instagram URL needs a stated reason to
  be believed this lead's, and an uncorroborated one is a **blank field, never a
  best guess**. A wrong address bounces and `email-verify` catches it; a wrong
  LinkedIn verifies clean, scrapes clean and produces a real, re-fetchable,
  quotable hook about a stranger, because `hook`, `hook-verifier` and `lint` all
  check the content and none of them checks *whose*. **Two people of the same
  name is not a find either** — an ambiguous match attaches nothing, the rule
  `corpus attach` already holds.
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
- **The orchestrator's context is the largest cost in a run, measured.** Across
  `2026-08-02-q2` and `q3`, **75% of every token spent was the main loop** — not
  the drafters, not the researchers. 410M tokens for 22 emails.
  **`cache_read` is the sum of the context over every turn**, so it falls with a
  smaller context and with fewer turns, and it grows quadratically when a run
  gets chattier and longer at once.
  **What the context is made of is now measured, not guessed** — `usage` prints
  it. On 2026-08-03: thinking 34%, tool results 31%, the model's own tool calls
  28%, and **prose to the operator 7%**. This file used to reason from
  "two-thirds is the orchestrator's own writing" — true, and it pointed the fix
  at narration, which is the smallest of the three. So: **fan out a whole wave in
  one message**, have every worker write its output to a file and reply with one
  line, let a command read those files rather than reading twelve objects into
  the loop, and keep tool calls small — a heredoc lives in the context as long as
  the run does. Narrate less too, but know it is worth 7%. None of that trades
  away a check; the money was never in the work.
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
  false pass costs one research call. Pass the lead's `observations` with its
  text and the activity floor settles from a real publication date — **upward
  only**, so a lead whose observations are all stale reads exactly like a lead
  with none, and better evidence buys the floor a `yes` and never a kill.
- `python main.py research <obj.json>` — schema. Catches a verdict outside the
  enum, and a hard yes/no with no source, which means it was reasoned rather
  than fetched.
- `python main.py observe <obs.json>` — the same treatment for what a worker
  says it actually fetched: enums, a piece of content that carries its text, a
  publication date that parses and has already happened, and a `retrieved_by`
  naming a rung this machine has. **The activity floor consumes them; nothing
  else does yet**, and the hook stage still does its own fetching. The contract
  exists so that evidence stops being discarded one boolean at a time, and so
  the duplicate fetch it makes unnecessary can be removed against a measurement.
- `python main.py plan <identity.json>` — which hook rungs a lead actually has,
  what each would cost, and which paid ones point at somebody else's channel.
  **A decline binds** (D28): `hook-worker` may not escalate onto one. It gates
  **spend and never inclusion** — a declined lead gets a null hook, a row and a
  Blocker, never a drop, and `plan` still exits 0 when every rung is declined.
  It shipped advisory for two batches because a gate beside its own measurement
  generates the data judging it; `metrics --plan` is that measurement and is why
  it could turn on. `unknown` is never declined. Pricing is opt-in.
- `python main.py select <research.json>` — ranks the observations already
  retrieved into a shortlist of three per lead, fetching nothing. Four of the
  twelve bans are mechanical here. **The hook stage reads this** (D27) — three
  candidates so a rejected first pick needs no second retrieval. `--against`
  survives with its verdicts re-read: `agreed` is rank 1, `shortlisted` is rank
  2 or 3, `missed` is a ban to re-examine, and **`unobserved` is the escalation
  rate**. A quote it finds is in the text we stored, never verified on the page.
  `--hook-room` takes the low end of the range `deal` prints. `--batch` commits
  the corpus beside the verdict, so a later ranking change is re-scorable.
- `python main.py hook <proposal.json>` — the hook, checked **before** an
  independent verifier certifies its wording. F4's gate: research and
  observations both had a schema and the one sentence a stranger reads first did
  not, so six of twelve drafts had to alter text a verifier had confirmed word
  for word. Every finding says **pick a different quote**, never edit theirs —
  one stage later the drafter has neither the alternatives nor the authority. It
  also refuses a LinkedIn post URL with an empty slug, which 404s however true
  the quote is. **`--against <select.json>` closes ban #3**: the quote must be a
  contiguous piece of the observation it names, which was unenforceable until
  the hook stage read a shortlist. A blank `observation_id` is legal only with
  `escalated` and a rung. **A pass is not verification** and the report says so.
- `python main.py lint <drafts.json>` — traceability, claim preservation, the
  bridge, voice, and batch repetition. **A figure in the hook beat that is also
  in the certified quote is exempt**: quoting is not claiming, and the rule
  written to stop us relabelling a client result was deleting the recipient's
  own facts out of the beat whose job is to prove we read their page.
- `python main.py export --anchors <deal.json>` — the drafts really used the
  lines the batch deal assigned, checked on both the reported id and the written
  text. A drafter that drew its own line ships an email that reads perfectly and
  a CRM row naming a sentence the reader never saw.
- `python main.py channel-find --leads <clear.json>` — the LinkedIn, Instagram
  and website a directory list arrives without. **Without `--execute` the plan
  prints and nothing is spent**, and `--leads` must be the CLEAR list from
  `dedupe --stage early` or it exits 2. Four verdicts, and three of them leave a
  field blank for different reasons: `NONE` found nothing, `UNCORROBORATED`
  found somebody and rejected them, `AMBIGUOUS` found two people of that name
  and nothing separating them. Chunking is for resume and blast radius, never
  for sliding under the cost gate. The state file keeps the raw SERP rows beside
  each verdict, so a rule change is **re-scorable without re-paying** — which is
  how three real defects were fixed after the live run at zero cost.
- `python main.py icf-intake <x.xlsx>` / `icf-export` — the directory source
  reader and the join back. The values that matter are cell hyperlinks, and the
  ICP prefill is a **hint file that settles no floor**.
- `python main.py email-check|email-verify|email-enrich` — address shape,
  deliverability, and the no-address fallback on their own branded domain.
- `python main.py dedupe` — exits 1 on a warm hit, exit 2 if the wall is
  unreadable. A missing wall file must never read as "nobody has been contacted".
- `python main.py copy-sync` — pulls the hand-written lines out of Airtable and
  **rejects any that fail the linter**, so an edit there cannot break an email.
  Writes nothing when anything fails.
- `python main.py copy-check` — the reader to `copy-sync`'s writer, run at the
  top of a batch. Asserts that the live Copy Assets lines pass the linter and
  that `copy/*.csv` still matches them. Exit 1 on either, exit 2 when it could
  not read the table. `deal` enforces the same thing at the moment lines become
  a batch's lines: exit 1 on a live edit that fails the linter with no override,
  exit 1 on an unreadable table unless `--allow-cached-copy`.
- `python main.py wall-add` — appends a shipped batch to the wall. Run it AFTER
  uploading, never before: walling a lead who never received anything would
  silently exclude them from every future batch. Idempotent.
- `python main.py copy-usage` — reports which lines actually shipped back to
  Copy Assets. Also after uploading. **Additive, not idempotent** — run once
  per batch.
- `python main.py crm-rows` — the Airtable Leads row, built in code. It joins
  the normalized Lead to the research object **explicitly and fails closed**,
  because twenty rows went in from the research file alone with no First Name,
  Last Name, Website, LinkedIn or City on any of them. It prints coverage for
  every field, not the ones anybody expects — the check that passed those rows
  looked at four populated fields and reported 20/20. It computes; **a human
  still writes**, which is `audit/airtable.py`'s boundary unchanged.
- `python main.py ledger` — what each retrieval cost and how long it took, one
  JSON line per fetch in `data/runs/<batch>.jsonl`, written as the run proceeds
  so a batch that dies mid-stage still leaves its accounting. `ledger batch`
  names the batch once and writes `work/BATCH`, so the label is discoverable
  rather than something twelve workers are told. `ledger add` records the
  model-side rungs Python cannot see, on trust; **`ledger pass` records the
  Claude bill** — agent passes by stage and by model, the cost nothing here
  could see until a batch spent ~64 passes on 20 leads and recorded the number
  64. `ledger report` reads a batch back and names any `(lead, url)` fetched
  twice for something other than verification. **Exit 2 on a missing ledger** — a missing ledger is
  not a zero-cost batch, the same asymmetry as the wall. **Never exit 1**, not
  even on a duplicate: reporting one is the job, and a gate that can halt a send
  file over an accounting line is a gate people learn to route around.
- `python main.py metrics <research.json>` — what the hook stage yielded and
  what the leads that yielded nothing cost: `hook_yield`, `refute_rate`,
  `null_hook_rate`, `yield_by_rung`, `wasted_retrieval`,
  `cost_per_verified_hook`. **A count nobody supplied prints `?`, never `0`** —
  the wall's asymmetry a third time, because a zero is a measurement and a block
  that zero-fills looks like evidence. `yield_by_rung` is the number that
  settles F5; `wasted_retrieval` is the one the retrieve-once work is trying to
  move. **`escalation_rate` is what judges the flip** (D27) — hooks the
  shortlist did not hold — and **`--plan` reports `declined_and_dry`**, which is
  D21's reversal condition and the evidence D28's decline gate turns on. It also
  prints the Batches row as a paste-ready block and **does not write it** —
  Python computes, a human still sees the row land. Exit 2 on an unreadable
  ledger, **never exit 1**, same rule as the ledger.
- `python main.py usage --batch <label>` — the Claude bill, **measured** from the
  session's own transcripts, against `ledger pass`'s **reported** counts. A pass
  is an invocation and says nothing about magnitude: q3 reported 185 passes
  accurately and could not say the batch spent 182M tokens, or that **75% of them
  were the orchestrator**, which reports no passes at all because nobody records
  one for the loop they are typing in. Tokens, not dollars — `record_pass` is
  right that prices go stale, and that argument is about prices. **Run it before
  the session ends**: transcripts die with the container, and the artifact is the
  only part that outlives them. Exit 2 on a shape it cannot read, never exit 1.
- `python main.py verdict <file>` — the cold read's schema, which did not exist
  until 2026-08-02. `problems[].beat` is an **enum** because a wave's findings
  are counted by it, and a REWRITE naming no problem is rejected: it would re-run
  a drafter against no instruction.
- `python main.py redraft work/ --out work/redraft.json` — who goes back, who
  holds, and **one shared note per beat several drafts failed on**. The one-repair
  cap is a loop bound here rather than a sentence; as a sentence it lost on both
  measured batches. Seventeen of seventeen q3 drafts failed on the same beat and
  were repaired individually, because nothing counted them — a reader going lead
  by lead cannot see the seventeenth until they have paid for sixteen. **Never
  exits 1 on a routing decision.**
- `python main.py collect <stage>` — builds `researched.json`, `draftable.json`
  and `drafts.json`, which no command produced before: the orchestrator
  serialised each out of its own context. `--expect` prints coverage and fails
  closed, which is `crm-rows`' lesson — a count of what was found is not a count
  of what should exist.
- `python main.py replies <export.csv> --leads <research.json>` — the manual
  Smartlead bridge, the only path here to reply data. Reply rate by `hook_type`
  and by rung, which is what `Hook Type` has been a CRM select for since the
  beginning. Columns are sniffed because nothing here has seen a real export; a
  column it cannot identify is **exit 2 naming the headers it saw**, never a
  zero reply rate. `--all-replied` is never inferred: a pre-filtered file and an
  unrecognised column look identical and differ by the whole answer.
- `python main.py doc-check` — the docs against the code they describe. Every
  command a doc names must exist in the parser, every path it backticks must be
  on disk, every copy-line id must be in the CSV, every `Defers to:` must
  resolve, and **no defining doc but `docs/spec/03-offer.md` may carry a
  price**. Exit 1 on drift, exit 2 if it could not run. It runs with the
  test suite, not with a batch — a doc typo must never be able to halt a real
  send file. It also checks the CRM's select options against the tuples that
  mirror them, which is the one authority this repo does not own; that half
  needs a key, says so when there is none, and `--live` makes a missing key
  exit 2 rather than a skip.

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

**And it is dealt before the hook is written, not after** (D24). The bank leaves
between 12 and 36 words for a hook, so dealing late handed the drafter a hook
that had been certified against a verbatim quote and then had to be compressed —
the four hand-written lines are never available to cut instead. A hook chosen to
fit is a citation; a hook squeezed afterwards is a citation drifting from its
source. The cost is that leads holding on a refuted hook leave their lines
unused, which is what `export --rebalance-ps` is for and which now fires on most
batches rather than some.

**The repetition cap outranks the 70/30 exact-match ratio.** When a segment has
too few identity lines to spread its share — Executive has exactly one usable
for an individuals-facing lead — the excess spills to generic rather than
putting one sentence in front of 70% of a batch. `deal` then prints a `THIN`
line naming the segment and how many more lines it needs. That is the fix; the
spill is the workaround.

## Key pieces

Pointers, not manuals. Every module carries a full docstring.

**`outbound/`** — `normalize` (raw row to Lead, junk classification),
`ig_intake` (an Instagram profile dump read as Leads **and** as the corpus it
already carries — a dump is a retrieval somebody else paid for, not input),
`triage` (RUN / HOLD / DROP before a cent is spent, on `qualify`'s own floors;
`unclear` is HOLD, and only a **complete** corpus may drop a lead on a stale
date),
`dedupe` (the two passes and the Contacted-Before wall), `fetch` (the free-first
ladder and the batched Apify plan), `resolve` (which channels are plausibly this
lead's own, and on what evidence — advisory, and it gates spend rather than
inclusion), `qualify` (the three floors, evidence-
carrying), `plan` (the hook ladder as data, per lead and priced — **the
authority on which rungs exist and in what order**, which `docs/hook-rules.md`
now names instead of listing), `research` (the typed contract every worker
returns), `observe` (one thing that was actually fetched, kept verbatim),
`select` (ranking over observations, and the measurement that says whether the
hook stage's fetch bought anything), `hook` (the proposal's schema and the voice
rules, run before certification rather than after), `anchors` (the
deterministic line draw and the fact table), `lint` (the checks), `export`
(leads.csv and preview.txt), `crm` (the Leads row, joined explicitly and failing
closed — it computes, a human writes), `ledger` (what every retrieval cost and
how long it took, plus the agent passes reported on trust — the only module here
that fails **open**, because an observer that can halt the run it observes is
worse than no observer), `metrics` (what the hook stage yielded, what the leads
that yielded nothing cost, and what the batch spent in agent passes by stage and
model — the same fail-open rule, and `?` wherever a count was not supplied),
`replies` (the manual Smartlead join, and the only thing here that touches reply
data).

**`audit/`** — what survived the pivot: `email_check`, `email_verifier`,
`email_enrich`, `apify` (cost-gated), `extract`, `urls`, `draft_lint`,
`footprint`.

**`copy/`** — **a cache of Airtable's Copy Assets table, not the authority on
anything.** `identity.csv`, `offer.csv`, `cta.csv` and `ps.csv` are regenerated
by `copy-sync` so the machine still runs when Airtable does not; they are the
last thing the table said, never a line somebody chose here. **Edit the lines in
Airtable, then run `copy-sync`, which validates and regenerates these files.**
`copy-check` is what keeps that true — it fails when a live line does not pass
the linter, and when these files no longer match the table.

`results.csv` is the exception and is repo-only on purpose: it is the fact table
every number in every email traces back to, and where the lines are voice that
gets tweaked, the results are audited evidence that should not be casually
editable.

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
- **A push runs the CRM schema check.** `.claude/hooks/schema_drift.py` fires on
  every Bash call, returns immediately unless the command contains `git push`,
  and then compares `audit/airtable.py`'s select mirrors against the live base.
  **Drift blocks the push; a failure to reach Airtable warns and allows it** —
  opposite defaults, because a stale mirror endangers a batch rather than a
  merge, and an outage must not hold every unrelated push hostage. It exists
  because CI has no key and this is where one lives.
- **Cross-session memory is `docs/journal.md`.** The container is ephemeral.
  When a session does anything worth remembering, add a dated entry at the top
  and commit it.
- **Firecrawl is gone** (2026-07-31). The fetch ladder is: local
  `requests` + BeautifulSoup (concurrent, `--workers`), then the agent's own
  WebSearch/WebFetch, then Apify for what is genuinely login-walled or that
  free HTTP could not read. **`python main.py fetch --escalate` runs the
  batched paid crawl**; without the flag the plan is printed and nothing is
  spent. `apify/cheerio-scraper` is the static path and
  `apify/website-content-crawler` the render path, and rendering is only ever
  correct for a page that returns 200 with no text.
- **Apify** needs `APIFY_TOKEN`. Every run is cost-gated at $0.10 and blocks
  with `APPROVAL REQUIRED` / exit 3 above it. **Check the budget once per batch,
  not once per worker.** Container boot dominates the bill, not pages — batch
  every URL into one run. Seven vetted actors; `yt_channel` and `search` were
  retired 2026-08-01 because one fed a field the ICP never gates on and the
  other duplicated the agent's own free WebSearch. Neither was a bill —
  **`audit/apify.py`'s rule is that an actor is surface area, not capability.**
- **Email verification** is one paid actor (`audit/apify.py` names it) and one
  free fallback, the local MX check in `audit/email_check.py`, used when Apify
  is near cap or `EMAIL_VERIFY_PROVIDER=local`. **The local check can prove a
  domain takes mail and never that a mailbox exists**, so its best answer is a
  WARN saying exactly that; only the paid verifier can clear an address. ZeroBounce
  is gone (2026-08-01): it was the documented fallback and had no credits when
  the outage finally called on it. **`email-verify-batch` is where an outage
  is visible** — a whole batch coming back inconclusive is not an address
  pattern, and it exits 2.
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
  **Every rung below the first records why it was taken** (`CopyBank.reason`,
  printed by `deal` and `anchors`), because all three interesting failures — a
  dead key, an unreachable base, and an edit that fails the linter — used to be
  swallowed into the same silent fall-through to the CSVs.
- **Smartlead** owns sending. No API key here yet; handover is a CSV Haytham
  uploads by hand.
- `pip install -r requirements.txt` to run the machine, `requirements-dev.txt`
  to also run the tests. No browser needed — Playwright went with the crawler.
- **CI runs `doc-check` and the suite on every push and PR**
  (`.github/workflows/checks.yml`). `doc-check` gets its own step even though
  the suite covers it, so a docs drift reports as a named failure printing its
  own line rather than a pytest traceback.
