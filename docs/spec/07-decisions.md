# Decisions

_Written 2026-07-31, seeded from what was already settled across the code, the
journal and the pivot. Everything here has been argued once. The point of the
file is that it does not get argued again by accident._

**Owns:** the decisions that are closed, and the condition that would reopen each
one.
**Defers to:** `docs/journal.md` — the session each decision was made in and what
it cost; `docs/spec/03-offer.md` — the pricing decisions, which are the offer
itself rather than entries here.
**Allows:** none.

## How to read this

Every entry carries **what would reverse it**. That field is what makes this a
decision log rather than a rules list. A decision with no reversal condition is a
preference, and preferences do not belong in a constitution — if you cannot say
what would change your mind, you have not decided anything, you have just gotten
used to something.

Reversing an entry is legitimate. Reversing one *without noticing it was decided*
is what this file prevents.

---

### D1 · The machine never sends
**2026-07-31.** The pipeline ends at a file. Smartlead owns inboxes, warmup,
ramp, sequence steps and replies; Haytham uploads.

**Why.** A pipeline that drafts and sends is one bad batch away from an
unrecoverable mistake across hundreds of real people. A pipeline that drafts and
stops is one bad batch away from a file nobody uploads. The gap between those is
a person reading the preview, and that gap is the product.

**Reversed by** nothing currently foreseeable. If it ever is, the preview gate
has to be replaced by something better first, not removed.

---

### D2 · Never act as Haytham anywhere
**2026-07-31.** No logging in to, acting as, or automating through Haytham's own
accounts on any platform. Read-only, no-login tools only.

**Why.** An identity rule, not a platform ban. Public data through a no-login
third party is fine, on LinkedIn and Instagram the same as anywhere. What is
forbidden is the machine wearing his face.

**Reversed by** nothing. This one is not a trade-off.

---

### D3 · Sell ten names, not a finding
**2026-07-31.** The email offers ten real people who fit the coach's buyer
profile, handed over on a call. It does not offer a diagnosis.

**Why.** The funnel auditor ran 589 leads and made nothing. Its reply rate was
good — 7-9% against a 1-5% benchmark — and **reply to call was 0 of 9.** Two
causes. It sold a finding, and a finding in an inbox is a free fix: 4 of 9
engaged leads read it, fixed it themselves and left. And its call to action was a
question, which selects for replies that are *answers*, and an answer is a dead
end that looks like success.

**Reversed by** a tested offer that beats it on reply-to-call, which is the one
number that has never been above zero. Not by a better reply rate — that metric
is already known to be a liar here.

---

### D4 · `unclear` passes
**2026-07-31.** Every floor verdict is three-valued. Only a clear `no` drops a
row.

**Why.** A false kill is permanent and invisible — the lead is gone and no report
will ever mention it. A false pass costs one research call and gets caught
downstream. Those errors have wildly different prices, so the gate tilts toward
the cheap one.

**Reversed by** research calls becoming expensive enough to matter, which would
mean the fetch ladder had regressed badly.

---

### D5 · A verdict with no source is not a verdict
**2026-07-31.** A hard yes or no on any floor must name what settled it. The
schema rejects it otherwise.

**Why.** An unsourced hard verdict was reasoned rather than fetched. Sourcing it
also makes a `no` arguable instead of something taken on trust, which matters
because of D4.

**Reversed by** nothing. This is the cheapest check in the machine.

---

### D6 · Dedupe before any paid call
**2026-07-31.** Name and domain first, email again after research. A warm-thread
hit stops the run.

**Why.** The previous pipeline deduped last and paid for eight enrichment calls
on an already-excluded lead. And a cold opener landing on a live conversation is
the only failure in this machine that destroys something rather than wasting
something.

**Reversed by** nothing on the warm-hit half. The ordering half is reversed only
if dedupe ever becomes more expensive than research, which would be strange.

---

### D7 · No agent certifies its own work
**2026-07-31.** Every stage making a consequential claim has an independent
verifier that never saw how the claim was reached and defaults to rejecting it.

**Why.** Under the old machine, a third of self-certified findings failed under
scrutiny while carrying a verified flag, and unread citations reached real
drafts. A single context checking its own work is not checking anything.

**Reversed by** nothing structural. The specific instances change as stages do.

---

### D8 · Research gets a schema, not a verifier
**2026-07-31.** Research is the one worker stage with no verifying agent. Its
claims are settled mechanically.

**Why.** A schema check is cheaper than an agent and strictly harder to talk
around. Spend an agent only on claims no regex can settle — whether a quote is
really on a page, whether a paragraph reads like a person wrote it.

**Reversed by** a class of research error the schema demonstrably cannot catch.
Note this is the specific application of a general rule: **prefer a mechanical
check to an agent, always.**

---

### D9 · Never invent a hook, and no hook found is a good answer
**2026-07-31.** A hook is a citation or it is nothing. A hook that cannot be
re-fetched and confirmed means the lead holds and gets no row.

**Why.** A fabricated hook is unrecoverable on the call and it poisons every beat
behind it. There is no volume target that justifies one.

**Reversed by** nothing. Volume pressure is the thing this decision exists to
resist, so volume pressure is not an argument against it.

---

### D10 · The hand-written lines are the anchor, and the linter makes that safe
**2026-07-31.** The drafting model writes against four lines a person wrote. It
may re-voice them so the beats connect; it may not change what they claim.

**Why.** This is the join between the two systems that merged. The cold-email
system had the right copy and a pipeline that stapled beats together mechanically,
so the hook never connected to the paragraph after it. The funnel auditor had a
chassis of fail-closed checks. Giving the model real freedom is only affordable
because everything it could get wrong is mechanically catchable.

**Reversed by** a drafting failure mode that the linter cannot express — which
would be an argument for a better check before it is an argument for less
freedom.

---

### D11 · Never invent a number, and never relabel one
**2026-07-31.** Every number in an email must be true of a real client result.
A number next to a named segment must belong to that segment.

**Why.** Two different failures — invention and relabelling — and either is the
tell that the whole email is fabricated, hook included. The results are real,
they come up on the call, and these coaches compare emails.

**Reversed by** nothing.

---

### D12 · A batch is dealt, not rolled
**2026-07-31.** Anchor lines are allocated across the whole batch at once.

**Why.** Per-lead hashing is unbiased only in the limit and batches are not that
big. Measured on the live lines, a 50-lead batch gave one offer line 8% against a
declared 20% and pushed another over the repetition cap. It converged near n=200.
Dealing gets the worst miss to about a point.

**Reversed by** batches getting large enough that the per-lead draw converges,
which is a change in how the business runs rather than in the code.

---

### D13 · The repetition cap outranks the exact-match ratio
**2026-07-31.** When a segment has too few identity lines to spread its share,
the excess spills to generic rather than putting one sentence in front of most of
a batch.

**Why.** Two coaches comparing notes and finding the same email is worse than one
coach getting a slightly less specific line. The spill is a workaround; the fix
is more lines in that segment, and the deal reports which segments are thin.

**Reversed by** filling the thin segments, which retires the situation rather
than the rule.

---

### D14 · The wall lives in the repo
**2026-07-31.** `data/contacted-before.csv`, not a CRM table.

**Why.** It is read on every run, never needs a view or a filter, and a network
hop is a strange dependency for the cheapest and most consequential check here.
Appending is a commit, so the wall has a history for free.

**Reversed by** the wall growing past what is comfortable to read on every run,
or by a second operator needing to write to it concurrently.

---

### D15 · Firecrawl is gone; the ladder is free-first
**2026-07-31.** Local `requests` and BeautifulSoup, then the agent's own
WebSearch and WebFetch, then Apify for what is genuinely login-walled.

**Why.** Two of the three rungs are free, and the paid rung is batched because
container boot dominates the bill rather than pages.

**Reversed by** the tier-0 fetch rate turning out to be low enough that the free
rungs are mostly wasted work. That number is unmeasured — see
`docs/spec/05-pipeline.md`.

---

### D16 · The audience and price floors were retired, for different reasons
**2026-07-31.** Three floors, not five.

**Why.** The audience floor became irrelevant when the offer changed; the price
floor was relevant but unmeasurable. `docs/spec/02-icp.md` holds both arguments
and the retired number.

**Reversed by** a floor that is *both* measurable and predictive, tested against
both failure modes rather than one.

---

### D17 · The journal starts at the pivot
**2026-07-31.** Everything from 2026-07-18 to 2026-07-30 was deleted, and the
separate archive file with it. Older entries get condensed in place, never moved
to a second file.

**Why.** The deleted log described a machine that no longer exists — Gmail
reconciliations, Loom offers, Notion migrations, a pipeline that was removed.
Three of those blocks loaded at every session start and were actively misleading,
because the hook does not know a pipeline was deleted, it just serves the newest
entries. A hand-maintained overflow file nobody loads is where detail goes to
rot, which is most of what the archive turned out to be.

**Reversed by** nothing. Git has it.

---

### D18 · Documentation is a layer with a gate
**2026-07-31.** `docs/spec/` states decisions and their reasons and holds no
value that something else owns. `python main.py doc-check` enforces the
mechanical half.

**Why.** The previous doc set rotted in three weeks, one reasonable copy-paste at
a time, and cost a commit literally titled *"Sweep the last stale prices and
rename the guarantee everywhere."* One of its five files survived, and it
survived by following this rule before it was written down.

**Reversed by** the gate producing more false alarms than drift, which would be
an argument for narrowing its rules rather than dropping the layer.

**The worked example this decision exists for.** The Apify cost ceiling is a
number, it is genuinely useful in `docs/spec/01-operation.md`, and the file is
forbidden to carry it. There are two ways to comply and only one is right:
declaring an `Allows:` exception is the failure mode wearing a permission slip,
because the number then exists in two places and only one of them can be wrong
without anyone noticing. Naming `audit/apify.py` instead is correct forever and
sends the reader somewhere that cannot lie to them. **When a value is tempting,
that is the signal to point at it rather than copy it.**

---

### D19 · The identity beat is claim-scoped; the other three are text-scoped
**2026-08-01.** Offer, close and ps are Haytham's sentences, lightly re-voiced.
The identity beat is **written per lead**, and what is fixed about it is what it
claims — which row of `copy/results.csv`, which columns, whether it may name the
segment — not its words. `outbound/anchors.py` owns the grammar; Airtable *Copy
Assets* holds the value.

**Why.** A defect in a hand-written line was unfixable by the drafter, who is
not allowed to touch the copy. The lead spent its one rewrite pass on a problem
it structurally could not solve and held anyway: two of three send-ready leads
died that way on the first real batch, and the fix each time was editing a line
in Airtable, per lead, forever. It was also already two-thirds true — the bridge
rule requires a second-person clause before the first digit and most bank lines
open on a bare stat, so the model was already composing that sentence on most
leads. What was missing was any check on what the composed sentence claimed, and
a wrong figure went out under a real segment's name for a month because of it.

**What it costs.** A mechanical guarantee that the identity words are Haytham's,
traded for a mechanical guarantee about the claim plus a human guarantee about
voice. The cold read is materially more load-bearing on this beat than on the
others, which is why `draft-verifier` watches specifically for a sentence that
carries the claim and none of the reference line's edge.

**Reversed by** authored identity sentences reading measurably worse on cold
reads than the hand-written ones did. Not by a single bad draft — by a pattern
across a batch that the verifier keeps catching.

---

### D20 · One email verifier, and no documented fallback nobody has run
**2026-08-01.** `michael.g/email-verifier-validator` via Apify, with the local
MX check in `audit/email_check.py` as the free fallback. `account56` and
ZeroBounce are deleted rather than disabled.

**Why.** Two verifiers were down at once on the first batch: the primary
answered `{"status":"error"}` for every address, and ZeroBounce — the
*documented* automatic fallback — turned out to have zero credits when it was
finally called on. The machine had no working verifier and said so only as a
WARN per address, indistinguishable from a run of catch-all domains, for 40
leads. A fallback nobody has exercised is a fallback nobody has, and a flag
saying "do not call this actor" is a call site waiting to be switched back on by
somebody who does not know why it was switched off.

The local check can prove a domain takes mail and never that a mailbox exists.
Its best answer is a WARN that says exactly that, and it can never clear an
address on its own. **No SMTP probe**, deliberately: cloud IPs are widely
blocked on port 25, the large hosts accept-all anyway, and a probe from a
container reads as reconnaissance to some mail hosts.

**Reversed by** a second verifier that is actually exercised on every batch
rather than only in an outage — which is the only way the next one gets found
before it matters.

---

### D21 · Ownership is typed, and it gates spend, never inclusion

**2026-08-01.** Every channel a lead has carries a `confirmed | absent |
unknown` verdict and the evidence that settled it. Nothing drops a lead on it,
and nothing ever will. What it will gate, when `plan` exists, is whether the
machine pays to scrape that channel.

**Why.** About 40 of 151 rows on the first real batch pointed at somebody else,
and three separate checks noticed — a note at intake, a report line after the
site read, and each agent improvising. All three were advisory prose that no
data structure carried forward, so every bad row was found by hand, one at a
time, after the money was spent.

Advisory is the correct posture for a *kill*: a false kill is permanent and
invisible, which is the same asymmetry that makes `unclear` pass the floors. It
is the wrong posture for a *purchase*, where a false pass costs one call and is
recoverable. Typing the verdict is what lets those two be separated at all.

The same asymmetry sets which way the rules lean. A URL harvested from a page
that names the lead is `confirmed` even though the page could be linking
somebody else, because in the gating direction a false `confirmed` costs one
scrape and a false `absent` costs a whole channel.

**And `unknown` never means the tell said no.** A handle mismatch is the only
path to `absent`. An opaque channel id carries no name to check, and calling
that a mismatch would fill the report with false negatives — which is how a
check becomes the line everybody scrolls past.

**Reversed by** a batch where declining to spend on low-confidence channels
costs more verified hooks than it saves scrapes.

**The gating half is live as of D28**, and that reversal condition is now
computable: `metrics --plan` prints `declined_and_dry`. The inclusion half is
unchanged and is not up for revision — nothing drops a lead on an ownership
verdict, and D28 restates that rather than qualifying it.

---

### D22 · A stage never re-fetches what an earlier stage read free

**2026-08-01.** `resolve` runs after `fetch`, consuming its site read, and the
only thing it fetches itself is the link-in-bio page that nothing else reads.
The retrieval proposal's own architecture diagram puts `resolve` first; this is
a deliberate departure from it, not an oversight.

**Why.** That diagram has no `fetch` stage at all — tier 0 has been absorbed
into a later phase there. Read as an instruction for the machine as it stands,
it means reading each homepage to harvest socials and then reading it again in
`fetch` seconds later: one duplicate `(lead, url)` per lead with a site, 89 of
151 on the first batch. The ledger would name every one of them, and the single
duplicate it was built to expose — the same LinkedIn profile scraped by two
different agents — would be buried in the noise. A signal people are trained to
scroll past is worse than no signal.

**Reversed by** tier 0 moving into the retrieval stage, at which point
`resolve`'s source for socials changes and the ordering follows it. The rule
itself does not reverse; only the stage that satisfies it does.

---

### D23 · The hook ladder is code, and the prose names it

**2026-08-01.** Where a hook comes from — the four rungs, their order, which are
free, which are paid, which actor each names and which of them can share a run —
lives in `outbound/plan.py` as `LADDER`. `docs/hook-rules.md` keeps what it
actually owns: what a hook is, the four requirements, the twelve bans, the two
windows and the three types. It names the module instead of listing the rungs.

**Why.** The ladder was prose in two files kept in agreement by hand, and the
agreement has failed twice, both times recorded in the file it failed in. The
list once opened with the **paid** LinkedIn rung under a heading that said "in
cost order", so the sentence and the list disagreed and the list won — which is
how a batch reaches for LinkedIn before reading an About page already on disk.
And the recency window existed as four different numbers in four files before it
was collapsed into two owners. Neither drift was caught by a check, because
nothing in this repo reads a paragraph: `doc-check` can prove a command exists
and can never prove two lists agree.

It is also the one part of the hook stage that has to be **per-lead**. A rung
nobody has a channel for is not a rung, and prose cannot say so. Making it a data
structure is what lets `plan` report which rungs are populated and what each
would cost, and it is the precondition for `yield_by_rung` — the number Part 8 of
the proposal calls the one that settles F5.

**What this does not do.** `.claude/agents/hook-worker.md` still carries its own
copy of the ladder and is deliberately not edited: the hook stage keeps fetching
until `select` has been measured against it, and rewriting the agent's routing
would be the behaviour change this phase is built to avoid. So there are two
copies today rather than one, and the second is implementation-layer prose that
`docs/spec/00-index.md` permits to describe how current code works. It goes when
the hook stage stops fetching, and not before.

**Reversed by** a batch where the generated rungs are wrong often enough that an
agent improvising would have done better — which would mean `resolve`'s channel
verdicts are the thing to fix rather than the ladder's shape, so the reversal
points at a different file than the one it would revert.

---

### D24 · The lines are dealt before the hook is written

**2026-08-01.** `deal` runs on the draftable set, between the late dedupe and
the hook stage. The `HOOK ROOM` it prints goes to `hook-worker` as a budget and
to `select --hook-room`. It used to run one stage later, after every hook had
been found and verified.

**Why.** The live bank leaves between 12 and 36 words for a hook depending on
the draw. Dealing afterwards meant a hook could be found, cited, and certified
by an independent verifier against a verbatim quote — and then handed to a
drafter with 12 words of room. `draft-worker` is explicitly forbidden from
trimming the offer, close or ps lines, because those are somebody's
hand-written sentences and `hook_room` is calculated on the assumption they
survive intact. So the only thing it could compress was the one sentence the
machine had just gone to the most trouble to certify. **A hook that is chosen to
fit is a citation; a hook squeezed after certification is a citation drifting
from its source**, and nothing downstream re-checks it — the verifier has
already run.

**The cost, stated rather than discovered.** Lines are now allocated to leads
that later hold on a refuted or inconclusive hook, so their four lines go unused
and the shipped batch drifts from the declared weights. That is R4 of the
proposal, and it needs no new machinery: `export --rebalance-ps` exists for
exactly this and the batch skill already instructs passing it whenever any lead
held. What changes is frequency — it fires on most batches now rather than some,
and the drift it reports is a line for the brief. Re-dealing after the hooks is
not the fix: the drafts and the CRM rows are written against the file `deal`
produced, and a second allocation makes them disagree.

**Reversed by** a batch where the ps rebalance cannot hold the repetition cap
after the holds — which would mean the drift is too large to absorb downstream,
and the answer is more identity lines per thin segment rather than a return to
dealing late. Dealing late does not become correct again; it only stops being
the worse of two problems.

### D25 · A check that can be mechanical must not cost an agent pass

**2026-08-01.** Where a rule can be enforced in Python, it is, and the agent
stage that used to catch it stops being the place it is caught. `hook` checks a
proposal before a verifier is spent on it, `check_batch` sees a template that no
per-email reader can, `crm-rows` replaces a hand-written script and the audit of
it, `--escalate-only` replaces re-running a whole stage to retry one call, and
`ledger batch` replaces telling twelve workers to remember a label.

**Why.** Batch `2026-08-01-q1` cost about 64 agent passes for 20 leads and 5
shipped rows, and until `ledger pass` existed nothing in this repo could say
which stage that was. That blindness is the same one F12 named for retrieval,
one layer up — and it is worse, because a fetch at least leaves an Apify
invoice. The rule matters beyond cost: **a mechanical check runs the same way
every time**, and an agent asked to remember a rule is an agent that will
occasionally not. Every gate this repo has was built on that reasoning; this
entry says the reasoning also applies to what a stage *costs*.

**What it does not license.** Replacing a *judgement* with a check. The cold
read caught 11 of 12 identity beats that had passed the linter, and every one
of those drafts was `LINT PASS` — voice is not mechanisable and the proposal
refuses twice, in writing, to optimise the verifier. The saving comes from
passes nothing has to run, never from a cheaper reader.

**Reversed by** a mechanical check that starts producing false findings people
route around. A gate that has to be argued with is worse than the agent pass it
replaced, because the agent could be told the exception and the gate cannot.

### D26 · The P3 flip stays off, and the batch that would decide it is not this one

**2026-08-01.** `hook-worker` keeps fetching, `plan` keeps declining nothing,
`select` stays advisory. The proposal's P3 is unchanged and still switched off.

**Why.** The measurement ran and reported 4 agreed, 3 missed, 5 unobserved over
12 verified hooks — and both halves of it turned out to be artefacts rather than
findings. **All three MISSED were one ban**, `site_prose`, which was 21 of the
corpus's 32 rejections and which the same batch disproved: those three
observations were `kind: about` and each had been independently VERIFIED. **Four
of the five UNOBSERVED were a flag**, not a capability: research ran `apify
li-posts --max 5` with no window while the hook stage ran `--since 3months`, so
the hook stage kept finding posts research had never requested. The `DUPLICATE`
half was polluted twice over — a retry that re-read every site, and an
observation nudge in five of twelve worker prompts.

Both causes are fixed (D25's rung flags, and ban #1 narrowed). Neither fix
produces a number: the corpus it would be scored against lived in `work/`, which
does not survive the container, so the batch that disproved the ban cannot be
re-scored against the correction. **`select --batch` now writes the corpus
alongside the verdict** so that this is the last time.

**Reversed by** one clean batch — run after both fixes, with no observation
nudge and no re-read retry — reporting `unobserved` and `missed` apart. If
`unobserved` stays high the fetch is not removable and the answer is research
fetching deeper, which is what the number pointed at before the flag was found.

**REVERSED the same day by D27**, without that batch. See below — this entry
stands as written because the reasoning in it is still the reasoning, and what
changed is who decided to act on it.

### D27 · The flip is on, taken on the diagnosis rather than the measurement

**2026-08-01.** P3 lands, all three switches. `hook-worker` stops fetching and
chooses from `select`'s shortlist; `select` runs before the hook stage and is
consumed; a `plan` decline binds. `hook-verifier` is untouched.

**Why, stated exactly.** Haytham's call, made after reading D26. The corrected
`unobserved` number **still does not exist** and could not be produced, because
the corpus that would be re-scored lived in `work/` and did not survive the
container. So this is a decision to act on the diagnosis — that both blocking
numbers were artefacts with known, fixed causes — rather than on the measurement
that diagnosis predicts. That is a legitimate call and it is a different one
from what D26 recommended, which is why it gets its own entry instead of an edit
to that one.

**What makes it recoverable rather than a guess.** Everything the flip could
break is now counted. `escalation_rate` is R1: the shortlist not holding.
`refute_rate` changes meaning and becomes sharper — post-flip a refuted quote
means the *stored text* did not match the page, which is a research-stage
failure reaching the reader. `null_hook_rate` and `hook_yield` are the headline
pair, unchanged. And `select --batch` now commits the corpus, so the next batch
is re-scorable even if the one after it changes the ranking.

**What did not move, and must not.** `hook-verifier` still re-fetches the cited
page live. Its independence was always the mechanism; post-flip it is also the
*only* check that a stored observation was ever real, because the worker no
longer reads the page it cites. Letting it read the observation instead would
save one fetch and retire the only thing in this system that has ever caught a
fabricated claim (R2).

**Reversed by** the next batch's numbers, and the three failures have three
different answers: a high `escalation_rate` means research must fetch deeper,
not that the ranker is wrong; a high `refute_rate` means observations are being
summarised rather than kept verbatim; a high `null_hook_rate` with neither means
selection genuinely cannot replace the search and P3 was wrong.

### D28 · A decline binds, and it ships with its own evidence

**2026-08-01.** A `plan` step whose channel is `absent` is declined for real:
`hook-worker` may not escalate onto it. `unknown` is still never declined.

**Why now and not before.** D21 established that an ownership verdict may gate a
purchase where it may not gate a kill, and `plan` shipped advisory for two
batches on the explicit reasoning that a gate shipped alongside its own
measurement generates the data that judges it. That objection was not dropped —
it was paid off. `metrics --plan` reports, of the leads carrying a declined
rung, how many produced a verified hook and how many produced none, which is
D21's reversal condition in D21's own words.

**The half that does not change.** A decline gates **spend**, never inclusion. A
lead whose every paid rung is declined still gets researched, still gets a plan,
still gets a row and a Blocker, and gets a null hook rather than a purchase.
`plan` exits 0 when every rung on a batch is declined, because exit 1 there
would turn an ownership verdict into the inclusion gate D21 forbids.

**Reversed by** `declined_and_dry` showing that declined leads produce verified
hooks at about the rate everyone else does — which would mean the ownership
verdict does not predict the waste, and `plan` should not gate on it at all.

### D29 · The hook's date comes from the source, and an undated source takes none

**2026-08-02.** `outbound/hook.py` no longer requires a `published_at` from
every proposal. It takes the date from the observation the proposal cites:
required and matching when the source carries one, **empty when the source
carries none**, and a non-empty date on a dateless source is rejected as
fabricated. Where no source can be joined — no `--against`, or a declared
escalation — the old rule stands and a date is required.

**The defect.** `select` offers About pages on purpose: ranked below everything
datable, so a lead sees one only when nothing recent survived.
`docs/hook-rules.md` has always allowed it ("an About-page line they wrote
themselves is fine at any age"). But `hook` demanded a date from every proposal,
and an About page has none. So a worker holding a legitimate fallback had two
moves: abandon the hook, or invent the date.

**Two workers invented it.** On `2026-08-02-q2`, independently, on different
leads, both wrote **today's date for a page that has none**, and one cited the
other's file as precedent. The only date rule was "not in the future", so a
stand-in of today cleared every mechanical check in the machine. Both were
caught by hand and withdrawn before export. That is very likely also how the
three VERIFIED About-page hooks on `2026-08-01-q1` were dated.

**An impossible instruction gets resolved dishonestly, and that is a gate defect
rather than a worker defect.** The first attempt at this fix banned About pages
from the shortlist instead, which removed the symptom and the fallback together
and was reverted the same day. The ranker was doing its job; the gate was not.

**What it buys.** Replayed against the batch's committed corpus, both withdrawn
proposals are now rejected with `carries no date at all`, and both are accepted
once their `published_at` is empty. The fabrication became mechanically
detectable in the same change that made it unnecessary.

**The half that does not change.** `EVERGREEN_KINDS` still exempts `about` and
`framework` from `select`'s date rules, `KIND_RANK` still ranks `about` last,
and ban #6 still applies in full to everything with a date. A missing
`published_at` **key** on a shortlist entry is treated as unknown rather than
undated — `resolve.py`'s "`unknown` never means the tell said no", one stage
over — so an incomplete record can never convict a worker of inventing a date.

**Reversed by** a batch where undated evergreen hooks are refuted by the live
verifier at a materially higher rate than dated ones, which would mean the
recency the date was standing in for was load-bearing after all, and the
fallback should be narrowed rather than dated honestly.

---

## What is unknown

- **Nothing here has been reversed yet.** The reversal conditions are untested,
  and a condition nobody has ever met is a guess about what would matter.
- **This file cannot tell a decision from a habit.** An entry nobody has
  questioned in six months may be load-bearing or may be inertia, and reading it
  will not tell you which. The reversal condition is the only handle, which is
  why every entry has one.
