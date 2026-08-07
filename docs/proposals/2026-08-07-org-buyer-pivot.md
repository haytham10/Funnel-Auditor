# Proposal: the org-buyer pivot

_Written 2026-08-07, on the `pivot` branch, from a discovery session that read
the defining layer and measured four things against committed batch data. This
is a **proposal**, not a decision. Nothing in it has been implemented and
nothing in `docs/spec/` has moved. A later session turns it into a phased plan._

**Owns:** nothing. A proposal is an argument, and the decisions it argues for
land in `docs/spec/07-decisions.md` if they are taken.
**Defers to:** `docs/spec/07-decisions.md` — every decision named here, whether
upheld or reversed; `docs/spec/04-email.md` — what an email is until this is
taken; `outbound/lint.py` — the checks as implemented; `copy/results.csv` — the
client results every number traces to; `outbound/plan.py` — the hook ladder.
**Allows:** none.

---

## 1. What this is

The machine is being repositioned onto one vertical — **UAE executive and
leadership coaches who sell high-value coaching or leadership development to
organizations** — and made dramatically cheaper to run.

The largest change is the email's shape. **Subject and hook are dynamic; the
whole body is static**, hand-written once. One vertical, one template, so a
campaign can be read. That single change retires the per-lead copy-allocation
subsystem and the drafting stage behind it.

The static body lives in a file written by hand on 2026-08-07, referred to
below as the template file. It is an input to this proposal, not an open
question. **It is not yet committed to this repo** — hence plain text rather
than a backticked path, per the doc contract's own convention for a name that is
a record rather than a pointer. Committing it is phase 1's first commit.

### What is already settled and is not re-litigated here

The market, the outcome sold, the email's new shape, the fourth qualification
floor, that sourcing enters the machine, that the ten-account deliverable is
built by hand after somebody books, that follow-ups are Smartlead's, and the
5M-tokens-per-shipped-email target. This proposal designs around those; it does
not argue about them.

### What does not bend

The machine never sends. Never act as Haytham anywhere. Never invent a hook, a
channel or a number — no hook found is a good answer, and an uncorroborated URL
is a blank field. Dedupe before any paid call, and a warm hit stops the run. No
agent certifies its own consequential work. The human preview before upload
stays.

---

## 2. Findings

Four measurements, all made against data already committed to `data/runs/`. They
are the reason several sections below say something different from what was
expected going in.

### 2.1 The template checks out mechanically

Verified against the real linter rather than by eye:

- The static body is **exactly 70 words** by `lint.word_count`. The template
  file's own figure holds.
- The assembled range is therefore **82–95 words**, and `lint.WORD_MAX` is
  **95**. A 25-word hook lands exactly on the ceiling with zero slack.
  `lint.WORD_MIN` at 67 becomes vacuous.
- The identity claim resolves cleanly against the `Executive / Dubai /
  corporates` row of `copy/results.csv`: meetings 6, clients 2, `sells_to =
  corporates` backing the budget-holder qualifier. "6 meetings … 2 signed" is
  exact and no city is named.
- **There is no relabelling risk on a mixed list.** `lint.check_attribution`
  reads "executive coach" adjacent to those figures and resolves to the
  Executive row, which is the correct row. The sentence is a claim about
  Haytham's client, not about the reader, so it stays honest even when the
  reader is a career coach.

### 2.2 The hook budget is feasible, and the template file's own top risk is
probably overstated

The template file predicts `null_hook_rate` will rise because the hook narrows
from 12–36 words to 12–25, and names that as the first number to watch. Measured
against the real shortlist corpus in `data/runs/2026-08-03-icf1-select.json` and
`data/runs/2026-08-05-icf2-select.json` — 100 leads carrying a shortlist, 207
candidates, 2,024 sentences:

| | |
|---|---|
| median shortlist post | **128 words** — a quote is always an extraction, never the whole thing |
| sentences 8–19 words | **52%** of the corpus |
| leads whose shortlist holds at least one contiguous 8–19 word sentence | **94 of 100** |

A hook is a contiguous quote plus a short clause saying what you took from it.
At a 25-word ceiling that is one of their sentences plus about six of yours, and
the material exists on 94% of leads that reach the stage. **The constraint is
real and it is not the bottleneck.**

The honest limit on this measurement: it prices the *source* material. The
shipped hook texts lived in `work/`, which is gitignored and did not survive the
container, so no batch's actual hook lengths can be recovered. What can be said
is that the corpus supports the budget on 94% of leads, and that if
`null_hook_rate` rises sharply anyway the cause is upstream of length.

### 2.3 `sells_to` is measurable at a useful rate — and it is a negative filter

`qualify.classify_sells_to` already exists, reads the lead's own words and
returns a source label. Nothing gates on it. Measured across 114 real ICF UAE
leads:

| | icf1 (n=59) | icf2 (n=55) | combined |
|---|---|---|---|
| `corporates` → PASS | 32% | 18% | **25%** |
| `individuals` → DROP | 25% | 29% | **27%** |
| blank → PASS | 42% | 53% | **47%** |

`docs/spec/02-icp.md` sets the test a new floor must pass: **both measurable and
predictive**, tested against both failure modes rather than one. The price floor
was retired for reading `unclear` on ~94% of the market. At 47% unclear and a
real 27% cut, this floor is measurable at a rate that clears that bar
comfortably. Predictive is untested, and that is its reversal condition.

**The consequence to state before the first batch report says it:** with
`unclear` passing per D4, roughly **72% of a list still passes**. The floor
removes the quarter that provably is not corporate-facing. **It is a negative
filter, not a targeting mechanism.** Targeting comes from sourcing. Anyone
expecting the fourth floor to concentrate a campaign on corporate buyers should
stop expecting it here.

### 2.4 Four captured fields are dead weight, measured

Field population across the same 114 leads:

| field | populated | who reads it |
|---|---|---|
| `top_program_price_aed` + `price_source` | **2 / 114 (1.8%)** | nothing |
| `runs_certification` | 4 / 114 | nothing |
| `solo` + `solo_source` | 18 / 114 | nothing |
| `audience_size` + `audience_source` | 11/59, then 46/55 | nothing |

`audience_size` is the interesting one: a four-fold swing between two runs of
the *same source list* is not a property of the market, it is worker discretion.
A field that is collected differently on Tuesday than on Monday and read by
nothing is not cohort data, it is a fetch.

### 2.5 The cost split, measured

From `data/runs/2026-08-03-icf1-metrics.json`:

| | |
|---|---|
| total | 261.0M tokens, 20 emails shipped |
| **per shipped email** | **13.05M** (target: 5M) |
| orchestrator | 166.5M — **63.8% of the total** |
| subagents | 94.5M |

Agent passes per raw lead across the four measured batches: q1 3.2, q2 4.95,
q3 5.4. The number was rising.

---

## 3. What the new architecture makes unnecessary

### 3.1 The retiring surface

Confirmed retiring, with the reason in each case being that a static body has
nothing to allocate:

`deal`; the `anchors` per-lead draw; `EXACT_MATCH_RATIO` (the 70/30
exact-match ratio); `FIXED_LINE_SHARE_CAP` and the deal-time repetition ceiling;
`thin_segments` and the THIN warning; `echo_pairs`; `_resolve_length`;
`hook_room` and `authored_budget`; `export --rebalance-ps`; `line-usage.csv`;
`copy-usage` entirely; `export --anchors` with `check_dealt` and
`check_identity_claims`; `scripts/build_draftjobs.py`; **`draft-worker` and the
whole drafting stage**; `redraft`; and the per-lead half of `copy-sync`.

`crm-rows` loses exactly one field, `Anchor Lines`. `Hook Type` is
research-derived and survives.

### 3.2 The correction: `outbound/anchors.py` cannot be deleted

The module also owns `load_facts()`, `all_numbers()` and `claim_for()` — the
fact table and the claim grammar that `outbound/lint.py`, `outbound/export.py`,
`outbound/copy_sync.py` and the `facts` command all import. **Deleting the file
kills the numbers gate**, which is D11's only enforcement.

The fact table has to be extracted to its own module first. Only then does the
draw become deletable. This is a sequencing constraint on the work, not an
argument for keeping the draw.

### 3.3 `draft-verifier` survives, rescoped

It is the only agent besides `research-worker`, `hook-worker` and
`hook-verifier` that survives, and saying so explicitly matters because the
stage around it is being deleted.

**Its question becomes one question: does this hook land into the sentence that
follows it — "I made you a list of 10 UAE companies that should be hiring
you"?** Asked against **the assembled message**, never a reconstruction, because
the thing being checked is whether the join reads as one person wrote it. That
join is risk #3 in section 12 and nothing mechanical can see it.

---

## 4. Keep / modify / archive / delete

| Component | Verdict | Why |
|---|---|---|
| `intake`, `ig-intake`, `icf-intake`, `icf-export` | **keep** | unchanged; a list still has to be read |
| `dedupe` | **keep** | the warm-hit rule is untouched, and it now also sizes campaign 1 |
| `chunk` | **keep** | D34 matters more once a quota-driven source produces the pool |
| `triage`, `fetch`, `resolve`, `plan` | **keep** | untouched; the retrieval half of the machine is not what is changing |
| `research` schema | **modify** | four captured fields deleted, `sells_to` promoted |
| `qualify` | **modify** | a fourth floor |
| `select` | **keep** | its three ranked candidates become the REWRITE path's supply |
| `hook` / `hook-worker` / `hook-verifier` | **modify** | the worker gains the subject and a null-reason enum; the verifier is untouched |
| `deal`, the `anchors` draw, `--rebalance-ps` | **delete** | nothing to allocate |
| the fact table and claim grammar inside `anchors.py` | **keep, extracted** | it is D11's enforcement |
| `draft-worker`, `redraft`, `scripts/build_draftjobs.py` | **delete** | there is no email to write |
| `draft-verifier` | **modify** | one question, on the assembled message |
| `lint` | **split** | see section 5 |
| `export` | **modify** | emits `hook`, not `body`; see section 9 |
| `copy-sync` / `copy-check` | **modify** | one record instead of four tables |
| `copy-usage` | **delete** | there are no per-line counts to report |
| `copy/identity.csv`, `offer.csv`, `cta.csv`, `ps.csv` | **archive** | superseded by the template file |
| `copy/results.csv` | **keep** | the fact table; checked once rather than per email |
| Airtable *Copy Assets* | **archive** | retires with the per-lead draw |
| `crm-rows`, `ledger`, `metrics`, `usage`, `collect`, `brief`, `replies`, `wall-add`, `doc-check` | **keep** | accounting and state; `metrics` gains two fields |
| `verdict` | **keep, narrowed** | the cold read still returns a verdict; its `beat` enum collapses to the join |
| `outbound-draft` skill and its four references | **modify** | the five-beat drafting craft is gone; the hook and voice references survive |

**Nothing here is preserved because it is tested.** The four deleted captured
fields have 44 lines of schema and tests between them and zero readers.

---

## 5. `lint` does not mostly retire — it splits in two

This is D25's reasoning applied to a check rather than an agent: it preserves
every rule while making it cost nothing per email.

### 5.1 A one-time template check

Run when the template changes, and in CI. Carries every rule that used to run
per email on a beat that no longer varies:

`check_claims`, `check_echo`, `check_seam`, `check_identity_claim`,
`check_attribution`, `check_identity_pronouns`, `check_dangling_figure`,
`check_ask`, and the paragraph count.

Not one rule is lost. All of them stop being a per-email cost.

### 5.2 A thin per-email lint, on the assembled message

Each of these still has a live job, because the hook or the subject can break
it:

- **the word budget** — the tightest gate in the machine now, and the check most
  likely to fire
- **`check_voice_fragment` on the hook**: em-dash, bare links, jargon, weak
  closers, unseparated figures
- **`check_numbers` plus the `mask_quoted_figures` quote exemption** — the hook
  is now the *only* place a new digit can enter a body. This is the single most
  load-bearing per-email check that survives, and the exemption is what stops it
  deleting the recipient's own facts out of the one beat whose job is to prove
  we read their page
- `check_subject`, hook-missing, hook-length, and the sign-off
- **batch: the hook-shingle check becomes the primary template detector**, since
  the hook is now the only variable text. It should be promoted from warning to
  failure. Subject reuse stays a failure. The opening-shape check is now the
  same signal as the shingle — keep one of them.

### 5.3 Two batch checks must be deleted, not left in place

- The **fixed-line share cap** is *permanently violated* under one template:
  every line is 100% of the batch.
- The **bridge opening-phrase cap** is a permanent warning for the same reason.

A gate that always fires is a gate people learn to route around, and then it
protects nothing. Both go.

### 5.4 `check_bridge` has no job, for two reasons

The template file's reason is right: the identity sentence now follows a
paragraph that is entirely second person, so it no longer needs a second-person
clause before its first digit.

The stronger reason is that the sentence is **static and read by a human once**.
There is nothing per-email for the check to catch.

Deleting it touches `outbound/lint.py` (the definition and its single call), the
rationale comments in `check_identity_claim` and the seam check,
`outbound/anchors.py`, the bridge batch check, the tests, `CLAUDE.md` and the
`outbound-draft` skill. Note that `copy_sync.validate` never ran it, so this
removes the rule from the pipeline entirely — which is correct here and would
not have been before.

---

## 6. The word ceiling: `WORD_MAX` is now the tightest gate, and it is inherited

At 70 static words, **every word of the ceiling above 70 is hook budget and
nothing else.** `WORD_MAX = 95` therefore sets the hook ceiling at 25 with zero
slack.

`docs/spec/04-email.md` says outright that 67–95 is *"inherited, not measured —
where the good drafts landed, not a number anyone A/B tested."* It was measured
on a five-beat email that no longer exists.

Deriving the range from the template is necessary and not sufficient. From the
same corpus as section 2.2:

| hook ceiling | quote must fit (with a ~6-word clause) | usable sentences | leads with ≥1 |
|---|---|---|---|
| **25** (`WORD_MAX` 95) | ≤19 words | **52%** | 94 / 100 |
| **35** (`WORD_MAX` 105) | ≤29 words | **69%** | 97 / 100 |

**Proposed: `WORD_MAX = 105`, hook budget 12–35.**

**Why.** At 95 the machine spends its tightest gate rejecting citations for
length. That is precisely the failure D24 exists to prevent — a hook drifting
from its source under length pressure — arriving through a different door. A
22-word quote that is the *right* quote dies before anything judges whether it
is good. At 105 the assembled email is still four paragraphs and still under a
screen, and the static body, which is the part a reader actually has to
tolerate, has not moved by a word.

**What would reverse it:** a measured reply rate showing longer assembled emails
perform worse; or the cold read beginning to reject long hooks as dossiers,
which would mean the ceiling was doing editorial work ban #8 should be doing.

**And this is the cheapest lever on `null_hook_rate` in the whole machine** —
one constant, no retrieval, no agent pass. If campaign 1 comes back with a large
`over_budget` bucket, the fix is a number rather than a re-architecture. That is
the strongest argument for the reason enum in section 8.

Separately, the constants should stop being literals: `lint` measures the static
body from the template and derives the range, so an edit to the template cannot
silently break the ceiling.

---

## 7. The subject line

Today the subject is authored by `draft-worker`, gated by `lint.check_subject`,
and **absent from the hook proposal schema entirely**. That stage is being
deleted, so somebody else has to write it.

**Proposed: `hook-worker` writes it, in the same pass as the hook.** Priced
against the 5M target:

| option | cost | verdict |
|---|---|---|
| `hook-worker` emits it alongside the hook | **zero extra passes** — same agent, same context, the quote already in front of it | **proposed** |
| a separate subject agent | +1 pass per lead, ~57 on an icf1-sized batch | the most expensive way to buy an eight-word string |
| Python derives it from the hook | zero, but "echoed in the hook, never a bare question, sentence case" is judgement, and D25 explicitly refuses to replace a judgement with a check | no |

Two consequences to carry:

- `subject` joins the hook proposal schema, and the `hook` command runs
  `check_subject`, **so a bad subject fails before a verifier pass is spent on
  it.** That is D25's exact shape.
- **`hook-verifier` does not verify the subject.** It re-fetches a citation.
  Widening its job is what D27 refuses, and its independence is the only thing
  in this system that has ever caught a fabricated claim.

**One known hole closes here.** The code records that digits banned from the
body can be smuggled into the subject, *"which nothing digit-checks"* — both
drafters on `2026-08-01-q1` did exactly that. With the body static, **the
subject becomes the only unchecked place a number can reach a reader.**
`check_numbers` must extend to it.

---

## 8. The cold read: what it costs, and what a REWRITE does

### 8.1 Agent passes per lead, priced

| stage | passes / lead | model |
|---|---|---|
| `research-worker` (a slice of ~10) | 0.1 | inherited |
| `hook-worker` (now also writes the subject) | 1.0 | inherited |
| `hook-verifier` | 1.0 | inherited |
| **`draft-verifier`, rescoped** | **1.0** | **Opus** |
| `draft-worker`, `redraft` | **0** | deleted |
| **total, per attempted lead** | **~3.1** | |

On an icf1-shaped batch that is roughly 177 passes, against the measured trend
of 5.4 per raw lead on q3 — a **40–45% cut in passes**, and the two deleted
stages were the expensive half of the run. `docs/agent-orchestration.md` records
that the drafting loop cost more than every other stage combined on q3.

### 8.2 The cold read is the one pass this proposal refuses to optimise

Its prompt shrinks a great deal on its own: it now reads one static body,
identical on every lead, plus one hook, and answers one question instead of
critiquing five beats.

The obvious further saving is **batching** — the body is byte-identical across a
wave and only the hook moves, so one reader could judge ten. **This proposal
holds that back for campaign 1 deliberately.** The join is the untested thing, a
reader judging ten in a row anchors on the first, and D25's own "what it does
not license" is replacing a judgement with a cheaper reader. Batching becomes
available once campaign 1 has published a verdict distribution, and it is named
here as the next lever if 5M is missed.

### 8.3 The REWRITE path, which does not exist today

A cold read that fails used to route back to a drafter. There is no drafter.
`select` already produces three ranked candidates per lead, and D27's stated
reason for three is *"so a rejected first pick needs no second retrieval."* This
is what they are for.

- **REWRITE routes back to `hook-worker`, once.** It may re-voice **its own
  clause**, or take **candidate #2**. It may **never** alter the quote.
- **A clause-only re-voice needs no new verifier pass.** The citation has not
  moved and is already certified. Only a candidate switch re-runs
  `hook-verifier`. A retry therefore costs 2 passes, or 3 if the candidate
  changes.
- **Bounded at one round.** A second REWRITE, or a REJECT, **holds the lead with
  no row.** That is D9's "no hook found is a good answer", one stage later. The
  one-repair cap is a loop bound rather than a sentence, which is `redraft`'s
  lesson and the reason it lost on both measured batches as prose.
- **Batch tripwire: if more than about a third of the first wave returns
  REWRITE, stop and surface it.** That is the template's join failing, not those
  leads' hooks. It is the existing quality tripwire in
  `docs/agent-orchestration.md` scaled to this stage, and it is the detector for
  risk #3.

---

## 9. The minimum first-campaign workflow

Stage by stage. "Existing" means the component runs today unchanged.

| # | Stage | In → Out | Mode | Component | Change | Gate |
|---|---|---|---|---|---|---|
| 1 | `ledger batch` | label → `work/BATCH` | auto | existing | none | — |
| 2 | `intake` | raw CSV → Leads | auto | existing | none | profile read aloud |
| 3 | `dedupe --stage early` | Leads → CLEAR | auto | existing | none | **exit 1 on a warm hit stops the run** |
| 4 | `chunk` | CLEAR + enrichment → batch + held-out | auto | existing | none | exit 1 on a lead the enrichment lacks |
| 5 | `email-verify` | addresses → verdicts | auto | existing | **WARN counts as reachable, and stays flagged** | exit 2 on a batch-wide inconclusive |
| 6 | `fetch` → `resolve` → `plan` | Leads → channels, rungs, costs | auto | existing | none | cost gate at $0.10, exit 3 |
| 7 | `research` | slices → typed objects + observations | agent | existing | **slimmed schema**, `sells_to` now load-bearing | schema, fails closed |
| 8 | `qualify` | research → four verdicts | auto | existing | **fourth floor** | exit 1 on a clear `no` only |
| 9 | `select` | observations → 3 ranked candidates | auto | existing | `--hook-room` becomes a constant | exit 1 only on its own schema |
| 10 | `hook-worker` | shortlist → hook **+ subject** | agent | existing | **writes the subject; records a null-reason** | — |
| 11 | `hook --against` | proposal → pass or findings | auto | existing | **runs `check_subject`**, before a verifier is spent | exit 1 on any finding |
| 12 | `hook-verifier` | citation → VERIFIED / REFUTED / INCONCLUSIVE | agent | existing | **none** | defaults to refuted |
| 13 | `assemble` | template + `first_name` + hook → the message | auto | **new**, trivial Python | — | zero agent cost |
| 14 | `lint` | assembled message → pass or failures | auto | **split** | section 5 | exit 1, fails closed |
| 15 | `draft-verifier` | assembled message → SEND / REWRITE / REJECT | agent | **rescoped** | one question, section 8 | one bounded retry |
| 16 | `export` | survivors → `leads.csv`, `preview.txt` | auto | **modified** | section 10 | a failed email is *absent*, not flagged |
| 17 | **preview** | ten emails, in full | **manual** | existing | renders the assembled message | **the gate no check replaces** |
| 18 | `crm-rows`, `wall-add`, `copy-check`, `metrics`, `usage` | accounting | auto | existing | `metrics` gains two fields | exit 2 on unreadable, never exit 1 |

**What should not be collected yet:** anything about the ten target accounts
(built by hand after a booking), follow-up copy (Smartlead's), reply-side
attribution beyond what `replies` already sniffs, and per-segment copy variants
— the campaign is testing one template and a second variant would make the
result unreadable.

---

## 10. Export, the preview, and the drift class this accepts

**The decision taken:** export emits the hook, and the static body lives in the
Smartlead campaign step, so all four sequence emails sit in one place.

Columns become `email, first_name, last_name, website, linkedin_profile,
location, subject, hook` — still eight, with `body` replaced by `hook`. The
spelling `linkedin_profile` is load-bearing and does not change: the wrong one
still imports successfully and silently lands as an extra custom variable.

**What this costs, stated in full because nothing here can see it:**

> The template in the repo and the template in the Smartlead campaign step can
> disagree. Every gate in this machine passes on a body that never ships, and
> `outbound/export.py`'s stated invariant — that the preview is byte-for-byte
> what leaves — is no longer true. The preview becomes a rendering of what
> Smartlead is expected to assemble.

Three mitigations, none expensive:

1. **`export --template`** prints the exact paste-ready string, so the Smartlead
   step is populated from the repo rather than retyped.
2. **The template's hash is recorded in the batch metrics** alongside
   `source_list`. A drift is then dateable — you can say which batches shipped
   which body.
3. **`preview.txt` renders the assembled message**, hook slotted in, and prints
   the hash it rendered against. The human gate keeps reading whole emails,
   which D1 requires.

**And the trade recorded honestly, for whoever reads this in six months.**
Mitigation 3 has the preview assembling the full message anyway — so the machine
already holds the template and already renders it, and emitting the assembled
body as a ninth column would be **one additional string write**. The
byte-for-byte invariant is not expensive to keep here; it is being given up
cheaply. The reason is an operator argument and a good one: all four sequence
emails live in one place, and email 1 not being the odd one out is worth
something to the person maintaining the campaign. **This was a choice about
where the copy lives, not a cost the architecture forced.**

---

## 11. The minimum data schema

Research's downstream jobs are: settle the floors, supply hook evidence, carry
the address, and populate the CRM row. Every retained field names one.

### Kept

| field | what it supports |
|---|---|
| `uae_based`, `is_coach`, `active_recent` + their three sources | the floors; CRM `Qualified` / `Failed Floors` / `Evidence` |
| **`sells_to`, `sells_to_source`** | **the fourth floor** (promoted) |
| `email`, `email_status`, `email_source` | `ready_to_draft`, the export column, CRM |
| `observations` | the entire hook stage — `select` ranks them and `hook-worker` quotes them |
| `name`, `slug` | the joins |
| `hook`, `hook_type`, `hook_source_url`, `hook_quote`, `hook_date`, `hook_verified` | the hook stage and `metrics` |
| `last_activity` | the activity floor's second route |
| `notes` | blockers |

### Deleted

| field | evidence |
|---|---|
| `top_program_price_aed`, `price_source` | 1.8% populated; the retired price floor still costing retrieval |
| `runs_certification` | 3.5% populated; no reader |
| `solo`, `solo_source` | 16% populated; no reader |
| `audience_size`, `audience_source` | no reader, and a four-fold swing between two runs of the same source |

### Demoted

`coach_type` and `coach_type_source`. `docs/spec/02-icp.md` calls it *"the only
captured field with a live job"* — picking the identity line. One template, one
identity line, so that job is gone. It survives as a **CRM cohort column only**,
off every gate, and it is what sizes campaign 1 in section 13.

**Stated rather than slipped in:** deleting those four means the retired audience
and price floors can never be revived from stored data, and cohort analysis on
them becomes impossible for future batches. The trade is four retrieval targets
per lead against an analysis nobody has ever run. If the cohort value is wanted
later, capture them only when they are free — already on a page the worker read
— rather than as a target worth a fetch.

### The fourth floor's shape

`sells_to = corporates` → PASS. `individuals` → **DROP**. Blank or unclear →
PASS, per D4. A DROP must name its source, per D5. A source saying both falls
through to blank, which is how `classify_sells_to` already behaves and is the
right behaviour: `docs/spec/02-icp.md` requires `sells_to` be taken from their
own words and never inferred, and a coach who does both has not said they only
do one.

---

## 12. The decisions this pivot touches

Every entry is upheld, or reversed with a stated reversal condition. **A pivot
that voids a decision by drift is the exact failure the doc layer exists to
prevent.**

| Entry | Verdict |
|---|---|
| **D1** the machine never sends | **upheld**, untouched. The preview gate survives and section 10 keeps it readable. |
| **D2** never act as Haytham | **upheld.** Sourcing is public, no-login only. |
| **D3** sell ten names, not a finding | **upheld.** The ten narrow to companies plus who inside owns the decision — a narrowing of the deliverable, not a change of offer. Reversal condition unchanged: a tested offer that beats it on reply-to-call. |
| **D4** `unclear` passes | **upheld and extended** to the fourth floor. Section 2.3 states the consequence. |
| **D5** a verdict with no source is not a verdict | **upheld and extended** to the fourth floor. |
| **D7** no agent certifies its own work | **upheld.** `hook-verifier` untouched; the cold read survives, rescoped to the one join no linter can see. |
| **D8** research gets a schema, not a verifier | **upheld.** |
| **D9** never invent a hook | **upheld**, and it now also governs the REWRITE path's terminal state. |
| **D10** the hand-written lines are the anchor, and the linter makes that safe | **Reversed in mechanism, upheld in principle.** The lines stop being something a model writes *against* and become the message itself, un-revoiced. The linter's job on them moves from per-email to once. **Reversed by** a single static body reading measurably worse on cold reads, or performing worse on reply rate, than the dealt-anchor variety did. |
| **D11** never invent a number, never relabel one | **upheld, and cheaper** — checked once on the template plus per-hook. Section 3.2 is the sequencing constraint that keeps it enforced. |
| **D12** a batch is dealt, not rolled | **Reversed by removal.** There is nothing left to allocate. **Reversed by** re-introducing more than one template, at which point allocation returns and dealing still beats rolling for the same measured reason. |
| **D13** the repetition cap outranks the exact-match ratio | **Reversed by removal — and this one must not go quietly.** The cap existed because *"two coaches who compare notes and find the same email is a worse outcome than one coach getting a slightly less specific line."* **One template makes that outcome certain.** This is not a side effect to absorb; it is the campaign's central bet, and the template file says so. **Reversed by** a reply that names the template, or two prospects comparing notes. |
| **D16** the audience and price floors were retired — three floors, not five | **Reversed to four floors**, on the measurement in section 2.3. **Reversed by** the new floor failing the same test the old ones failed: it is measurable at 27%/47%, so the live question is whether it is *predictive*, testable by reply rate split on `sells_to`. |
| **D19** the identity beat is claim-scoped, the other three text-scoped | **Reversed by removal.** The identity beat is no longer written per lead; it is one hand-written sentence. The claim grammar survives as a build-time check on the template. **Reversed by** returning to more than one identity sentence. |
| **D21** ownership is typed, gates spend never inclusion | **upheld**, untouched. |
| **D24** the lines are dealt before the hook is written | **Reversed by removal, reason preserved and strengthened.** There is no deal. But its argument — *a hook chosen to fit is a citation; a hook squeezed afterwards is a citation drifting from its source* — survives and gets better: the budget is now a **constant known before the batch starts** rather than a per-lead draw. Section 6 is that argument applied to the ceiling itself. |
| **D25** a check that can be mechanical must not cost an agent pass | **upheld and extended.** The `lint` split in section 5 is this entry applied to a check rather than an agent, and section 7 puts `check_subject` before the verifier for the same reason. |
| **D27 / D28** the retrieval flip; a decline binds | **upheld, untouched.** Hook retrieval is not redesigned. |
| **D32** Instagram is a corpus, not a source list | **upheld, and load-bearing for the sourcing phase.** Its lesson is reachability, and the sourcing quota must count **reachable** candidates — which is what a stop condition requiring a corroborated LinkedIn and a non-dead address already encodes. |
| **D34** a batch is cut by evidence, and the leads it leaves out are written down | **upheld, unchanged**, and more important once a quota-driven source produces a pool rather than a curated list. |

### New decisions this proposal asks for

| | |
|---|---|
| **The ps beat is deleted.** | The template carries no ps. `docs/spec/04-email.md` argues it is load-bearing — *"the beat that makes not replying cheap, which is what makes replying honest"* — and that argument is being overruled by the template, deliberately. **Reversed by** a reply rate materially below the 1–5% benchmark with no other explanation, since a costless no is the cheapest thing to add back. |
| **The beat order changes: the offer comes before the proof.** | The spec's fixed order puts identity second because it assumes the offer is a *claim*. Here the offer is an object that already exists, so showing it first is stronger — and it dissolves the bridge problem. **Reversed by** cold reads finding the proof sentence reads as a non sequitur where it now sits. |
| **`WORD_MAX` moves to 105.** | Section 6. **Reversed by** longer assembled emails measuring worse on reply rate, or the cold read rejecting long hooks as dossiers. |
| **The export drops the assembled body.** | Section 10, with the drift class and its three mitigations. **Reversed by** a shipped batch found to have used a Smartlead body that differed from the repo's template. |

---

## 13. Phasing, and what campaign 1 runs on

**Phase 0 — extract the fact table.** `load_facts`, `all_numbers` and
`claim_for` move out of `outbound/anchors.py`. Nothing else can be deleted until
this lands (section 3.2).

**Phase 1 — the smallest thing that produces a reviewed export file.** Commit
the template; add `assemble`; split `lint`; set the new ceiling; delete `deal`,
the draw and the drafting stage; rescope `draft-verifier` and wire the REWRITE
path; `hook-worker` gains the subject; export emits `hook`. Run it on **8–10
leads from the campaign-1 population below**. **Ends at a file Haytham reads and
does not upload.**

**Phase 2 — the fourth floor and the schema cut.** Independent of phase 1 and
deliberately after it, so campaign 1 is not blocked on a qualification change.

**Phase 3 — instrumentation.** The null-hook reason enum, the template hash in
`metrics`, reply rate split by `sells_to`. Small, and it is what makes campaign
1 readable. **Campaign 1 ships at the end of this phase.**

**Phase 4 — sourcing.** SERP discovery to a quota, on the already-vetted
`apify~google-search-scraper` — batched, cost-gated, `countryCode=ae` — and the
corroboration ladder `audit/channel_find.py` already implements in the other
direction. Its rules carry over unchanged: an ambiguous match attaches nothing,
a path segment is not a handle, a stated foreign location is a different person,
and **a SERP snippet never becomes an observation.** Campaign 2 is the first one
sourced by the machine.

### What campaign 1 actually runs on

Sourcing is phase 4, so campaign 1 is **hand-assembled from the executive and
leadership slice of the ICF lists already on disk**, not from a general held-out
slice. Counted exactly across `2026-08-03-icf1` and `2026-08-05-icf2`:

| | |
|---|---|
| `coach_type` is Executive or Leadership | 61 |
| minus individuals-only (the fourth floor) | 50 |
| minus already on `data/contacted-before.csv` | **39** |
| of those: address PASS 37, WARN 2 | all reachable, WARN counting as reachable and staying flagged |

**39 leads are in hand against a target of about 50.** The gap is roughly 11
hand-sourced before campaign 1 runs, which is an afternoon and not a phase.

This matters beyond logistics. Validating phase 1 on a general coach list would
prove the machine on the **wrong population** and land the 5M measurement on a
non-representative batch. The two things campaign 1 tests — the template, and
cost per email under the new architecture — are only readable if the leads are
the new ICP. **Both numbers come off the same 39.**

The honest limit: 39 is a small denominator. At a 1–5% benchmark it can tell you
the template is catastrophic. It cannot tell you it is good.

---

## 14. The dangerous assumptions, ranked by what they cost if wrong

**1. One template, every lead, no variation, is the campaign.** If it is wrong,
the whole campaign is wrong and nothing in the batch will say which part. That
is the price of cutting to one variable and it is the point — but it means the
first campaign's blast radius is the whole hypothesis. ~50 leads is the agreed
size, and section 13's denominator caveat is part of this risk, not separate
from it.

**2. That 5M is reachable by deleting stages.** It is not, on the measured
split. Deleting the drafting stage removes agent passes, which live in the 36%
subagent bucket. **The orchestrator's 64% falls only if the run has fewer turns
and a smaller resident context.** Deleting draft, redraft and the verdict wave
does that structurally — fewer waves, fewer files read back, no repair loop —
but a defensible floor is **6–9M, not 5M**. Getting under 5M likely needs the
change `CLAUDE.md` already mandates and icf1 did not hold: every worker writes
its output to a file and replies with one line, and a command reads those files
rather than the loop reading twelve objects. **If this is wrong, every
simplification scored against 5M is scored against a number nothing can hit**,
and work gets cut that should not have been.

**3. The hook flows into an offer sentence it was never designed to precede.**
Every hook rule — ban #9 especially, *"the hook must have a writer in it"* — was
written so the **identity** beat has somewhere to start. The sentence after the
hook is now "I made you a list of 10 UAE companies that should be hiring you."
Whether a writer-clause still does its job in front of *that* is untested. It is
exactly the join the rescoped cold read is being asked to judge, and the
one-third-of-a-wave REWRITE tripwire is its detector.

**4. That `sells_to` is predictive.** Measurable at 27% drop / 47% unclear, per
section 2.3. Predictive is unmeasured and is the floor's whole reversal
condition. If it is not predictive, the fourth floor is a 27% cut that buys
nothing and costs a retrieval per lead.

**5. Smartlead template drift.** Accepted with reasons, mitigated three ways,
still real — and it is the one failure class in this design that no gate in this
repo can detect.

**6. Sourcing recall against the fourth floor.** If the SERP pool is mostly
individuals-facing coaches, the quota keeps buying pages to feed a gate that
drops them. Partly handled, since the stop condition already counts only
candidates whose cheap ICP signals returned no clear `no`.

**7. The narrowed hook budget.** Ranked last on purpose. The 94%-of-leads
measurement in section 2.2 is why it moved down, and section 6's ceiling is the
one-constant fix if it still bites.

---

## 15. What would refute this

- **A cold read that keeps returning REWRITE on the hook-to-offer join.** More
  than about a third of a wave means the template's second sentence cannot
  follow an arbitrary hook, and the fix is the template rather than the hooks.
- **`null_hook_rate` rising with a large `over_budget` bucket.** That refutes
  section 6's ceiling, not the architecture, and the fix is a constant.
- **`null_hook_rate` rising with `over_budget` near zero.** That refutes section
  2.2's reading of the corpus and points at retrieval, which is D27's territory
  and not this proposal's.
- **Cost per shipped email landing above ~9M after phases 0–3.** That refutes
  risk #2's floor and means the orchestrator's context, not the stage count, is
  the whole problem — in which case the next work is the file-and-one-line
  worker protocol, not more deletion.
- **A batch report showing the fourth floor dropping far more or far less than
  ~27%.** The measurement is two ICF lists. A directory is not the market.
- **Any reply naming the template, or two prospects comparing notes.** That is
  D13's reversal condition arriving, and it means variation has to come back.
- **The 39 leads not surviving `dedupe` at the rate section 13 assumes.** The
  wall is the authority and it is read at run time; these counts were computed
  against a snapshot.
