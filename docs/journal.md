## 2026-07-31 (the first real batch) — 13 leads, end to end

Haytham dropped a real list and said run all 12. Every number below is measured,
not estimated, and every bug below was found by running the machine rather than
reading it.

**The funnel, stage by stage.** 13 rows in. Dedupe caught 1 (Salma El-Shurafa,
already contacted, cold). Tier 0 read **9 of 12 sites free (75%)**, 5k to 86k
characters each, and planned 2 batched Apify escalations rather than 12 separate
ones. All 12 passed the three floors. **11 of 12 hooks found and independently
verified (92%), zero refuted**, one clean no-hook (Nicola Tate: site is an
unconnected Wix domain with no Wayback snapshot, newest LinkedIn post 137 days
old, nothing on podcast or Instagram). 11 drafted, all 11 passed the linter.

**Then the draft-verifier refuted 7 of 11.** That is the headline. The linter
passed every one of them, and a cold reader who never saw them written sent back
4 SEND and 7 REWRITE. It caught: three numbers stacked into one proof sentence
so it reads as a pitch deck; "I got an executive coach here 6 meetings", which
parses wrong on first read and does it on the credibility line; "on the last
run", which tells the reader she is in a batch one line before the email claims
the names were picked for her; a subject promising "the action step in your
framework" over a body that opens on a different quote entirely; and one genuine
stapled-beats failure where the drafter pasted the identity anchor in with no
bridge sentence in front of it. The worker/verifier split is the whole reason
this machine exists and this is the run that earned it.

**Four bugs, three of which would have shipped.**

1. *The website column never mapped.* The list used `companyWebsite`; the alias
   table did not know that spelling, so 13 of 13 sites mapped to nothing and the
   entire free site-read tier was skipped in silence. Added the sales-export
   spellings, and `intake` now prints the columns it ignored.

2. *Tier 0 crashed on the first page of the first site.* `extract_emails`
   returns two buckets in a dict and `_harvest` called `list.extend()` on it,
   which iterates the keys — so `read.emails` filled with the strings "personal"
   and "generic" and died on `.get`. Unreachable with an empty page list, which
   is what every existing test had. `tests/test_fetch.py` now feeds real HTML
   through the real harvest, and the buckets stay apart until the end so a jane@
   on page four still outranks an info@ on page one.

3. *`coach_type` came back empty for 3 of 12 real headlines* — "Career and
   Work-Life Balance Coach", "Chief Executive Officer Coach" — because the
   patterns wanted the segment word adjacent to "coach". Added a loose pass
   allowing words between them, restricted to the headline and tried only after
   every strict pattern fails.

4. *Eight of the thirty-one identity lines carried "her" or "him"*, which
   `check_identity_pronouns` blocks — a quarter of the identity bank could not
   ship as written, and every drafter dealt one had to notice and silently
   rewrite it. Same class as yesterday's cta-02: `copy-sync` validated numbers,
   attribution and claims but never ran the pronoun check. It does now, and the
   eight lines are fixed in Airtable.

**Two findings that only a reader could produce, one now mechanical.** The cold
reader caught `b4-01` ("Not a scraped list") dealt alongside `ps-01` ("not a
list") — the same denial twice in ninety words. Neither line is at fault, so the
check belongs on the pair: `check_echo` now rejects any email whose offer, cta
and ps repeat a distinctive phrase. It fires on exactly 1 of the 16 offer/ps
combinations, and both test fixtures were using that pair, which is how common it
is. The second finding has no mechanical fix yet: `id-any-6` is a research
anecdote rather than a client result, and it was the one draft with no bridge —
it may only be safe on a lead whose hook is already about market opacity.

**A hazard worth naming.** Three draft-workers returned invented email addresses
in their JSON (`andy@theteamspace.ae` for a `.com` lead, and two others). Nothing
asked them for an address. The export takes the address from the lead record, so
nothing shipped wrong, but an orchestrator that trusted the worker's field would
mail the wrong person. Drafters should not be emitting addresses at all.

Final: 10 of 13 in the upload file, Cheryl held on the echo check, Nicola held on
no hook, Salma held on the wall. 337 tests green. Apify spend for the whole
batch stayed inside the $29 cap at 25.6% before the run.

## 2026-07-31 (last pass) — the hardening run, and the gate that was rejecting its own copy

Haytham: "do a final run over every part... make sure the system is ready,
bulletproof, and each part is synced." Two audit agents plus a full end-to-end
run on a synthetic five-lead list. The end-to-end run is what found the worst
one, which no static read would have.

**The machine was dealing lines its own linter rejected.** `cta-02` promised the
10 names and a same-day clock but never said *why those ten* — so `check_claims`
rejected every email it was dealt to, and `b4-04` never used the word "names",
failing the same check. Between them they silently condemned a share of every
batch, and the rejection line pointed at the draft rather than at the line that
caused it. `copy-sync` validated numbers, attribution, em-dashes, weights and
segments, but never asked whether a line carried its own beat's claim tokens.
It does now, and it fails closed. Identity is exempt on purpose: 22 of its 31
lines open on a bare stat, and turning that toward the reader is the drafting
model's job by design.

Repaired both lines in Airtable (the runtime source of truth — editing the CSVs
alone would have been overwritten by the next sync, and the live ladder was
still dealing the broken text), then ran `copy-sync --live` so Airtable, the
snapshot and the committed CSVs agree again.

Fixing `cta-02` made it 7 words longer, which exposed the next thing: the hook is
the only beat nobody writes in advance, so it absorbs every other beat's growth.
Added `_check_hook_room` — the longest line in each beat must still leave 12
words under the 95-word ceiling. Checked on the worst case, because the draw
picks the combination and nobody gets to avoid it. The live bank passes with 12
to spare, which is tight enough to be worth knowing.

**The false-kill surface in `check_uae` was much bigger than the DXB case.** The
rule was "X is not in UAE_CITIES", which is a statement about our list, not about
the lead. Measured it against 29 real UAE localities: eleven returned a hard NO,
including Al Barsha, Deira, Mirdif, Motor City and Emirates Hills. Every one of
those is a Dubai coach telling us exactly where she is. The burden now sits on
the kill: a NO needs a match in `FOREIGN_PLACES`, and an unrecognised place is
`unclear`, which costs one research call. Added the districts to `UAE_MARKERS`
too, so they pass rather than merely survive.

**`name_key` sorted its tokens**, so "Ahmed Mohammed Ali", "Ali Mohammed Ahmed"
and "Mohammed Ahmed Ali" were one key — three different men in a market where
given names double as surnames, and a permanent invisible kill for two of them.
The only case sorting bought was the inverted export, which is now handled by
un-inverting the comma. The sorted key survives as `loose_name_key` with
asymmetric consequences: it stops the run against a **warm** contact, and merely
reports a `NameEcho` against a cold one. That asymmetry is the whole design in
one function — a cold opener on a live thread destroys a conversation, a second
cold email months later wastes a send.

**Dead code that turned out not to be dead.** `extract_dates` had no caller;
rather than delete it, wired it into `qualify.latest_activity_date`, which
settles the active-in-30-days floor from page text instead of asking a worker
whether a page feels current. Two bugs found while doing it: the copyright filter
read the ±80-char context window, so a footer `©` discarded every date on the
page (which is every page — `extract_dates` now also returns the tight `near`
window it actually tested), and a year-less date would read a three-year-old
"March 14" as this March. `extract_availability` really was dead and went with
the audit — it made an un-buyable offer machine-visible, which was a *finding*,
and findings are not what this machine sells.

**`_rejoin_particles` was defined and never called.** Rewrote it as
`_joined_surname`, which ADDS candidates rather than replacing the surname: an
Al Fahim may use `alfahim@` or `fahim@`, and picking one silently loses the
other. Single-letter particles only rejoin when an apostrophe follows them in
the raw name, so "Jane L Smith" keeps `jane.smith@` instead of guessing
`lsmith@`.

Also: `write_batch`'s lint dict is keyed by email everywhere now (the test helper
was still on slug, which is the collision the fix was about); `draft_lint` and
`urls` had docstrings naming deleted modules as their consumers; and
`tests/test_cli_failures.py` is new — nothing pinned the exit codes the skills
quote, and exit 2 ("the check could not run") is the one that must never be
mistaken for exit 0.

326 tests green. End-to-end run writes 3 of 3 with the anchors held.

## 2026-07-31 (later still) — Copy Assets stopped being an inert table

Haytham: "the copy assets just sit there as a table, it shouldn't be a
bottleneck." Three things were true, and measuring first is what found the
second and third.

**1. Editing it had arithmetic homework attached.** Adding a fifth offer line
meant renumbering the other four roll ranges by hand so the spans stayed
contiguous, with a validator that failed the whole sync on a slip. Replaced with
a plain `Weight` on any scale, blank meaning equal share. Ranges are derived at
load, so the gap-and-overlap failure class is gone rather than checked. `Line ID`
now generates from the text when blank and `Word Count` is computed, so adding a
line is three cells: Beat, Line, Weight.

**2. The declared weights were fiction at real batch sizes.** Measured before
touching anything: independent per-lead hashing over the live offer lines gave
`b4-04` 8% against a declared 20% at n=50, pushed `b4-03` to 38% over the 35%
cap, and only converged near n=200. Added `deal` — largest-remainder allocation
over the whole batch. Worst miss at n=50 went 13 points to 1, and the cap is now
satisfied by construction instead of warned about afterwards. `anchors` keeps the
per-lead draw for single-lead work where there is no batch to balance.

**3. Nothing ever came back.** Added `copy-usage`, which reports which lines
actually shipped into `Times Used` / `Last Used` after an upload. The weights are
guesses today and usage plus reply data is the only thing that can replace a
guess with a measurement. Additive, deliberately not idempotent, unlike
`wall-add` — flagged in the output because the asymmetry could bite.

**Three bugs found while doing it, two of them pre-existing:**

- `exact_both + exact_type` put the same identity line in the pool twice
  whenever `sells_to` was `any`. That silently double-weighted those lines in
  the old per-lead draw, and made the batch deal issue more seats than there
  were leads. Deduped.
- **Alphabetical tie-breaking was systematically biased.** With 3 leads over 9
  equally-weighted identity lines every remainder ties, and sorting by id handed
  all three seats to `id-any-1/2/3` — so small segment groups never drew their
  matched line at all, which is the entire point of the pool. Ties now break on
  a hash of the id.
- **Dealing generics per segment clustered across the batch.** Six small segment
  groups each independently picked the same first generic line and put it in
  front of 42% of a 12-lead batch. The generic pool is shared, so it is now
  dealt once across the whole batch after each segment's matched share is taken.

**One content gap surfaced, not papered over.** Executive has exactly one
identity line usable for an individuals-facing lead, so a straight 70% match
rate put that sentence in front of 70% of the batch. The cap outranks the ratio,
so the excess spills to generic — but `deal` now prints a `THIN` line naming the
segment and the shortfall, because the spill is the workaround and writing
another line is the fix.

Copy Assets rebuilt (12 fields, seeded from Python rather than by hand) and
`audit/airtable.py` gained a narrow write path. 280 tests pass. Verified live:
deal → copy-sync → export → copy-usage → read back → reset.

### Open follow-ups
- [ ] Write a second Executive identity line for individuals-facing leads.
      `python main.py deal` prints the shortfall on any batch containing one.
- [ ] `Times Used` becomes useful only when reply data lands. Per-line reply
      rate is the number that turns the weights from guesses into measurements,
      and it needs Smartlead replies flowing back.

## 2026-07-31 (later) — Airtable read wired, wall moved to the repo, Smartlead columns pinned

Four asks, and two real bugs found while doing them.

**The Airtable read is a gate, not a copy.** `outbound/copy_sync.py` pulls Copy
Assets and validates every line before writing: numbers must trace to
`copy/results.csv`, no number may sit next to a segment it doesn't belong to,
and the weighted beats must cover 1-100 with no gap or overlap. Nothing is
written if anything fails. That last check was already needed and missing — a
gap in the roll ranges means some leads draw nothing and fall through to a
positional fallback nobody chose.

`anchors.CopyBank.load()` now tries live Airtable, then the last synced
snapshot, then the CSVs. `AIRTABLE_API_KEY` turned out to be live in the
environment after all, so the direct path is running today.

**Bug 1, found by the tests hanging: no cache.** `load()` fetched on every
call, so five draws made five HTTP requests. A 200-lead batch would have made
200 and tripped Airtable's 5-req/sec limit. Now cached per process, with
`OUTBOUND_COPY_SOURCE=csv` to force offline (the test suite sets it via
conftest, so the suite is network-free and doesn't depend on live data).

**Bug 2, found by round-tripping the real CSVs through a live fetch and
diffing: order changed the draw.** Airtable returns records in view order and
`draw_identity` indexes into the list, so the same lead drew a *different* line
depending on which source the bank loaded from. Deterministic within a source,
false across them. Fixed with a canonical sort by id everywhere; `copy/identity.csv`
is reordered in this commit as a result (content byte-identical, verified). A
test now asserts all three sources agree.

**Contacted Before moved to `data/contacted-before.csv`** — 104 rows, 9 warm —
and the Airtable table was deleted. Two walls that can disagree is worse than
either, and the dangerous direction is the repo one going stale while Airtable
looks current, since the repo one is what runs. It is read on every batch, never
needs a view, and appending is a commit, so the wall has a history for free.
`dedupe` now exits 2 on an unreadable wall rather than passing the batch.

**Export writes exactly eight Smartlead columns**: email, first_name, last_name,
website, linkedin_url, location, subject, body. Nothing analytical — that lives
in Airtable. It also writes `wall-additions.csv`, deliberately NOT applied:
nothing is sent at export time, and walling a lead who never received anything
would silently exclude her from every future batch. `main.py wall-add` closes
that loop after the upload, idempotently.

**Leads table rebuilt lean**, 34 fields to 28, grouped in the order the machine
fills them. Two real simplifications: the three floors collapsed into
`Qualified` (checkbox) + `Failed Floors` (multi-select), which is the query that
actually matters; and Status went 11 options to 7, with hold reasons living in
`Blockers` as text rather than as five near-identical statuses. New table ID
`tbl51dU7ojrxCVfxZ`. Copy Assets seeded with all 43 lines.

250 tests pass. The whole loop verified live end to end: live Airtable read →
copy-sync → intake → dedupe (stopped on a planted warm lead) → export →
wall-add → next batch blocks the walled lead.

### Open follow-ups
- [ ] `results.csv` is repo-only on purpose (lines are voice and get tweaked;
      results are audited evidence). Revisit if that friction bites.
- [ ] Move the Airtable base to its own workspace — the MCP can create a base
      but not a workspace, so it is in "My Workspace".
- [ ] Follow-ups (touch 2/3) still not built. Smartlead sequence steps; nobody
      has decided whether they should be per-lead personalised.
- [ ] First real batch still needs to measure the tier-0 fetch rate and
      reconcile Apify cost against the dashboard.

## 2026-07-31 — Rebuilt as an outbound machine: audit out, anchored AI drafting in

Merged the funnel auditor with the cold-email system Haytham had been running
separately. The auditor's offer is dead (589 leads, 0 AED, reply→call 0/9); its
chassis is not. The cold-email system's offer and copy are good; its pipeline
was not.

**What the merge actually is:** the hand-written copy lines became the drafting
model's ANCHOR rather than bricks it concatenates. The model authors the hook
and owns the seams between beats, and may re-voice an anchor for flow, but may
not change what the anchor claims. That is only safe because `outbound/lint.py`
makes every failure mechanical.

**Deleted** (~7,400 lines): crawler, evidence, vision gate, Gate 0 floors,
crm_gate, dashboard, send_cap, inboxes, touchlog, calendar_state, checks/,
config.py, the whole Gmail path, docs/leads (370 files), every funnel-audit
skill and agent. Firecrawl is gone from the environment, so the fetch ladder is
now local HTTP → WebSearch/WebFetch → one batched Apify run.

**Built:** `outbound/` (normalize, dedupe, fetch, qualify, research, anchors,
lint, export), `copy/` (the four line files + results.csv, the fact table),
skills `outbound-batch` and `outbound-draft`, agents research-worker,
hook-worker, hook-verifier, draft-worker, draft-verifier. 209 tests pass.

**Two things the linter caught that I had wrong**, both worth remembering:
- The first version rejected `id-corp-1` and `id-any-5` — real hand-written
  lines that *widen* a Business result to "coaches here". Widening is explicitly
  sanctioned; the failure is only relabelling (a number next to a segment it
  doesn't belong to). Split into `check_numbers` (invention) and
  `check_attribution` (relabelling).
- Periods needed exact unit equivalents: "60 days" and "2 months" are the same
  fact, and a checker that only knows one rejects an honest line. Approximations
  are deliberately NOT licensed — 45 days is not 6 weeks.

**Airtable:** new base `appejF07kunksqt4D` ("Outbound Machine") — Leads,
Batches, Copy Assets, Contacted Before. Seeded Contacted Before with all 103
previously-contacted leads from the old CRM, 9 flagged warm (Ben Pringle,
William Brown, Lucia Csobonyei, Lee Harris, Lisa Hugo, Avneet Kohli, Rita Baki,
Wafa Bassili, Donna Brown). Old base `appaBExqyEZykb1Qk` is archive only.

**ICP narrowed to three measurable floors:** UAE-based, is a coach, active in
30 days. Audience and program price are captured, never gated — audience
decoupled from the offer once we started selling her clients rather than
leverage on her list, and a price floor reads unclear on ~94% of coach sites.

### Open follow-ups
- [ ] Smartlead column names, so `export.py` writes them exactly. Currently
      `email, first_name, last_name, full_name, company, subject, body` + lead
      fields.
- [ ] Move the Airtable base to its own workspace (the MCP can create a base but
      not a workspace, so it landed in "My Workspace").
- [ ] Copy Assets table is created but empty and NOT yet read by `anchors.py` —
      `copy/*.csv` is authoritative. Wire the Airtable read, or drop the table.
- [ ] First real batch: measure the tier-0 fetch rate. Nobody has published what
      share of coach sites a plain HTTP fetch can read, and every cost estimate
      downstream depends on it.
- [ ] Reconcile that batch's real Apify cost against the usage dashboard. The
      last paper estimate was wrong by 6-7x.
- [ ] Follow-ups (touch 2/3) are not built. They are Smartlead sequence steps
      and nobody has decided whether they should be per-lead personalised.
- [ ] Sourcing is phase 2. Phase 1 is drop-a-list only.

# Project Journal — cross-session memory

The narrative git history and Notion don't capture: **what happened each
session** (pipeline ops AND dev), the decisions behind it, gotchas learned, and
open follow-ups. Notion holds live *state* (where each lead is); git holds *code
changes*; this file is the thread that ties sessions together so a fresh session
isn't starting cold.

**How it's used:** the `SessionStart` hook (`.claude/hooks/session_memory.py`)
injects the most recent entries here + the last few commits at the top of every
session, so context loads automatically — no fetch, no prompting.

**How to write it:** at the end of a session with anything worth remembering,
add a new `## ` block at the TOP (newest first), then commit + push. A
journal-only commit is fine on an ops-only session — the point is that it
survives the ephemeral container. Keep entries short and scannable: a few
bullets, then an `### Open follow-ups` list if any are outstanding. When an
entry's `### Open follow-ups` items are all resolved, cut the list rather than
leaving a stale all-checked block — the resolution belongs in whichever new
entry closed it out.

Entry template:

```
## YYYY-MM-DD — <one-line title>
- what happened (ops events, sends, sourcing, ticks, or code)
- decisions made and why
- gotchas / things that surprised us
### Open follow-ups
- [ ] the next thing someone should pick up
```

**Older entries get condensed, not deleted.** Once a day's entries scroll past
the "recent" window that's actually useful to load at session start, fold them
into one short dated summary here and move the full verbatim detail to
`docs/journal-archive.md` (not hook-loaded — manual lookup only). The full
2026-07-18/07-19 build-out is there as the first example; see the condensed
version below dated the same.

## 2026-07-30 — uae-tick: 32 follow-ups drafted, 6 unlogged sends recovered, freshness gate now blocking warm touch 4+

Scheduled daily tick, fresh session on `uae-track`. Large due-list day: 34
follow-ups due (9 Inbox 1, 25 Inbox 2) plus 2 stale-flagged warm leads.
Delegated the 27 formulaic cold Touch 2/3 drafts to 4 parallel background
agents (one per inbox slice); handled the warm/high-value threads and all
CRM reconciliation directly.

**Reconciliation gap found and fixed:** 6 sends from 2026-07-29 (William
Brown Touch 6, Rima Zanoun + Salma El Shurafa Touch 3, Sam Fouladgar +
Timothy Fare-Matthews + Tracy Harmoush Touch 2) had actually gone out in
Gmail but were never logged to Notion — Touch #, Last Contacted, and the
Email Thread Log all still showed the pre-send state. Recovered all 6 from
Gmail's real sent content (never fabricated), appended proper log blocks,
updated properties, ran `crm-gate log` (PASS on all 6). Rima + Salma's cold
sequence completed with no reply → moved to Dormant, revival bump
2026-08-13. **This is the same drift class as the 2026-07-26 24-lead
incident** (`crm-gate log` didn't exist yet as a per-write gate at the time
these went out) — worth checking whether the step 0.5 Gmail-state
reconciliation should extend beyond just Scheduled/Draft Ready rows, since
warm/cold follow-up sends never pass through either status and so never
get its Gmail-reality check.

**New systemic finding: the finding-freshness gate (3-day ceiling) now
blocks nearly every warm touch 4+.** The 2026-07-26 walk batch verified a
huge cohort of findings on one calendar day; today (07-30) is day 4, one
day past the ceiling. Confirmed FAIL on 4 separate leads today (William
Brown, Lucia Csobonyei, Avneet Kohli, Lee Harris) — all for the identical
reason, all from that same batch. The gate fires even when the touch's
carrier (call-ask, disambiguating-question) never actually restates the
finding, because `gate_send` checks `current_finding(row)` for any touch
past `COLD_SEQUENCE_TOUCHES` regardless of what the draft says. Held all 4
rather than draft around the FAIL. Fix is `refresh-finding` per lead, but
this will keep recurring for the rest of the cohort as they cross into
touch 4+ — worth deciding whether to batch-refresh the cohort or adjust
the gate to skip the freshness check for carriers that don't cite a
finding.

**Other:** `notion-query-data-sources` hit its usage cap partway through
(page-level fetch/update kept working, per the known workaround) — the
Sunday-collision hygiene sweep and the weekly scoreboard were skipped this
run. `log-lint` (distinct from `crm-gate log`) still fails on Rima's and
Salma's legacy Touch #2 line — a `(reply-in-thread)` annotation inserted
into the bracket-format subject breaks its regex; pre-dates this tick, not
fixed (would mean rewriting 9-day-old sent history for a linter quirk).

### Open follow-ups
- [ ] Run `refresh-finding` on the 2026-07-26 walk cohort's warm leads
      before their next touch, or teach `crm-gate send` to skip the
      freshness check when the declared carrier doesn't cite a finding.
- [ ] Dr. Daphne Soares + Libby Salord McLean (Inbox 2, Touch 1→2) rolled
      to tomorrow — Inbox 2 headroom was 23 against 25 due.
- [ ] Sam Fouladgar / Timothy Fare-Matthews / Tracy Harmoush Touch 3
      (disambiguating-question) falls due ~2026-08-03.

## 2026-07-29 — uae-tick: 7 due follow-ups drafted (both inboxes), stale Leak Fix language purged from uae-tick SKILL.md

Scheduled daily tick, fresh session on `uae-track`. `notion-query-data-sources`
silently caps SQL `SELECT` results at 100 rows with no `has_more` warning in
that mode — a first pull (WHERE Status NOT IN terminal states) returned
exactly 100 rows and looked complete, but a GROUP BY COUNT on the same filter
came back 120. Re-ran with `LIMIT 200 OFFSET 100` to get the missing 20,
which is how Lee Harris, Sam Fouladgar, Timothy Fare-Matthews, and Tracy
Harmoush turned up as due-today follow-ups that the first pass had silently
dropped. **Lesson: always cross-check a SQL-mode row count against a GROUP BY
COUNT(*) before trusting a query "looks complete," view-mode pagination
(`has_more`) doesn't apply to SQL mode.**

**7 due follow-ups drafted, all `crm-gate send` PASS, all held as Gmail
drafts (none sent):**
- Inbox 1: Lee Harris (Touch 5, warm, call-ask — pivots off the now-retired
  Leak Fix offered at Touch 4, finally names two specific times instead of
  the vague "whenever works" that stalled Touch 2-4).
- Inbox 2: Rima Zanoun + Salma El Shurafa (Touch 3, cold, disambiguating
  question — bank spent, sequence completes, no reply yet on either);
  William Brown (Touch 6, warm, call-ask — same vague-ask-to-named-times
  pivot as Lee); Sam Fouladgar, Timothy Fare-Matthews, Tracy Harmoush
  (Touch 2, cold, call-ask — first follow-up on each, kept finding-free
  since it's their second email ever and findings are never emailed).
  Inbox 2 landed at exactly 25/25 for the day after these 6 — no headroom
  left, but nothing had to roll since the due list matched the remaining
  slots exactly.

**Code/doc fix:** `.claude/skills/uae-tick/SKILL.md` section 2a still told
the turn-two queue to close on "the paid 48-Hour Leak Fix... or the
calendar link" — retired 2026-07-27, `crm_gate.py` only keeps it as a
deprecated alias for `call-ask`. Rewrote to the current call-ask-with-two-
times model. Also fixed a `second-finding` → `second-cold-read` mislabel
(with a duplicated "the the") in the Touch 2/3 carrier-picking paragraph —
the actual `CARRIER_CHOICES` list was already correct in code, only the
skill's prose had drifted. No functional bug (the CLI still accepted the
deprecated alias), but a tick reading this prose fresh could draft a dead
offer with a straight face.

**Reply sweep:** clean. Both inbox sweeps since the last tick (07-28) are
dominated by clearly unrelated inbox noise (HR-policy-reminder-shaped spam,
smartlead onboarding mail); none of the ~50 sender addresses match a UAE CRM
lead. One bounce (`lee@dubailifecoach.com`) doesn't match any CRM row
either — not ours to act on.

**Ceilings:** Inbox 1 25/day (ramp step 2, day 8 — RAMP REMINDER, eligible
for 30 if deliverability held, Haytham's call), Inbox 2 25/day (ramp step
2, day 5, next step eligible 07-31). Both inboxes were already at 19/25
before this tick ran (real Gmail sends from earlier today, all logged
correctly per the automated hygiene sweep — zero flags across all 120
non-terminal rows).

**Send queue (Touch 1 openers): empty.** Only one `Audit Ready` row exists
(Silvia Vladimirova, carried over from 07-28, still needs
`haytham-hook-finder` before a draft can exist) and one `Qualifying` row
(Nedal Mohamadeiah). Top-of-funnel is still thin.

**Hygiene:** clean sweep across all 120 non-terminal rows — no Touch#0 on
Outreach Sent, no cold Touch >=4, no Sunday-landing Next Action, no
future-dated Last Contacted, no bad Audit Ready rows, no un-turned-two
stale Reply Received. Avneet Kohli and Rita Baki both sit at exactly 2 days
since Asked For Price (not yet the >2-day flag threshold) — both already
correctly resolved/waiting, not stale. Scoreboard not due (last was 07-27).

### Open follow-ups
- [ ] Silvia Vladimirova (textalent.io) still needs `haytham-hook-finder` —
  carried over 2 ticks now.
- [ ] Run `source-leads`/`qualify-leads` — top-of-funnel still just 1
  Audit Ready + 1 Qualifying.
- [ ] Watch for replies on the 7 freshly-drafted follow-ups once Haytham
  sends them, especially Lee's and William's first-ever named-times call
  asks (both threads had only gotten vague "whenever works" asks before
  today).

## 2026-07-28 — The First Five v2: repriced to 2,000/900, re-niched to AED 5,000+, The Named Fifty added as the attraction offer

Haytham brought three documents from his Claude project — an offer study run
through the Hormozi skills, plus v2 cold-reads and v2 examples. The two copy
files were shippable as-is; the study was a decision packet. He took all three
recommendations after a recommendation-with-pushback.

**Shipped first (copy, independent of the pricing decision):**
- **`cold-reads.md` v2.** The v1 list was written against the funnel-fix offer:
  `price-invisible`, `no-aed` and `price-band` all observe how she displays a
  PRICE, which is a non-sequitur when the thing being sold is a booked call. A
  prospect reads beat 2 and beat 5 as one sentence. Six patterns now, every one
  terminating in an empty chair, `half-empty-week` leading. `COLD_READS`
  updated; `RETIRED_COLD_READS` added so a retired id fails with a redraft list
  rather than a bare "not sanctioned", and the CLI accepts the retired ids on
  purpose so the gate is what fails.
- **`examples.md` v2.** The four sent UAE openers (finding opener, question
  close, 9 replies / 0 calls) replaced by 12 worked examples of the current five
  beats, plus a 13th for the Named Fifty. Parenting examples untouched.

**The three decisions, and what each cost:**

1. **Repriced to AED 2,000 setup + 900/qualified call, billing from call one,
   no credit-back.** AED 600 is $163 — below the *basic* tier ($150-300, "a name
   and a slot") while delivering the top tier ($400-750, BANT-verified with
   no-show replacement). The credit-back gave away AED 1,800 of month-one cash
   for a concession Five or Free already buys. The "price never moves" rule was
   not violated: it exists to protect the read on a running test, and there was
   no test and no closes. Frozen now until two clients are delivered.
   Guarantees also changed: **The Empty Chair Guarantee** (renamed), and **Five
   or Free upgraded from a refund to a SERVICE guarantee** with the clock
   starting at FIRST SEND, not payment — domain warming ate two to three weeks
   of a 30-day window, which made the old wording close to unwinnable.
2. **Re-niched to a live program at AED 5,000+**, as Gate 0's fifth floor in
   `audit/gates.py`. Purchasing power is the market study's one measured FAIL.
   Two design decisions inside it: floating currencies get a **band**, not a
   rate, and the gate only rules when every rate in the band agrees; and a
   scraped price can **promote but never kill**, because application-only 1:1
   work is routinely off-page and a Gate 0 hard fail is permanent.
3. **The Named Fifty** (AED 500, 50 verified UAE contacts in 72h) as the
   attraction offer, `docs/uae-track/05-the-named-fifty.md`. Needed a new gate
   shape: `crm-gate offer --tier attraction` requires a LIVE THREAD instead of
   the earned right, because an attraction offer exists to buy a customer and
   the earned right would make it unsendable. Core tier unchanged and still the
   default, and it keeps the bare `CRM GATE (offer):` label because skills match
   that prefix.

**Gotchas:**
- Moving the price-floor helpers into `audit/gates.py` was forced, not stylistic:
  `evidence.py` imports Playwright, so anything living there is untestable in a
  managed session.
- **The `Program below AED 5000` select option was deliberately NOT created.**
  Notion creates a select option on first write, and a DDL `ALTER` would have
  rewritten the option list across 246 already-disqualified rows for a cosmetic
  addition. The first real price-floor kill creates it. `Top Program Price
  (AED)` (number) WAS added live — purely additive, zero risk.
- 41 new tests; suite green at 357.

### Open follow-ups
- [ ] **Test the cheap version of the Named Fifty premise first.** Example 8's
      "twenty names" call ask puts a deliverable in the call at zero build cost
      and tests the same hypothesis. Only build the AED 500 product if that
      moves reply → call.
- [ ] **Stand up 3 more warmed inboxes.** The Rule of 100 floor is 100 actions
      a day; we run 15-50 across two. This is the largest uncapped lever and
      everything else is a percentage improvement on a base five times too
      small. It cannot be fixed by raising a per-inbox ceiling.
- [ ] Re-pitch the six live warm threads (Dina, William, Avneet, Rita, Lee,
      Lucia) on the new offer. Human job.
- [ ] The two unsourced cold reads (`call-centric`, `waiting-room`) still need a
      fresh CRM count before they can ship.

## 2026-07-28 — Recalibration: `docs/START-HERE.md` added, stale finding-era text purged from the outreach method

Haytham said the pivot left him lost — the vision was clear before the offer
swap and is now blurry, and his Claude project is full of docs he can no longer
tell apart. Diagnosed as a doc problem, not a strategy problem: the strategy is
coherent, but three post-pivot documents still asserted the pre-pivot method, and
a retired doc that still claims authority keeps winning arguments after it's
dead.

- **New `docs/START-HERE.md`** — the single orientation page. Offer in one
  sentence, why it changed (the two mechanical causes: question-CTA can't book,
  a finding in an inbox is a free fix), the five beats of the opener, the machine
  in one line per stage, the five gates that fail closed, a canonical / advisory
  / historical ledger over every doc in the repo, and the one open bet
  (reply → call, still 0). Linked from the top of `CLAUDE.md`.
- **`04-the-outreach-method.md` was the worst offender and is now corrected.**
  It still told the reader to lead the opener with the verified finding, still
  had the free Loom as the turn-two artifact, and still named GSO v2 as the
  priced offer. Fixed: standard motion steps 2/3/7, Lane 1's opener line, the
  whole OPENER section (rewritten to the five beats), TURN TWO, WHEN THEY SAY
  YES, and THE ARTIFACT (marked RETIRED with the delivery-speed lesson kept).
  "The finding is what earns the reply" corrected to "specificity is what earns
  the reply" — the reply rate held, the carrier was wrong.
- **The three-tell heuristic** for triaging his Claude project offline: a doc is
  dead if it names a price that isn't 1,500 / 600, puts a finding in an email, or
  asks a lead what they'd pay.

### Open follow-ups
- [ ] Haytham to delete or archive the superseded docs in his own Claude project
      using the three-tell heuristic; the repo copies are now labelled.
- [ ] Nothing in the machine changed. The only number that matters is
      reply → call, still 0 of 9, with two live call-asks standing (Rita Sanna,
      Lucia Csobonyei).

## 2026-07-28 — uae-tick: 32-lead overnight batch reconciled, `crm-gate log` false-FAIL bug found and fixed, two live call-asks now standing

Scheduled daily tick, fresh session on `uae-track`. The entire 32-lead due-today batch (17 Inbox 1 + 15 Inbox 2 — every row with `Next Action` = 2026-07-28) had already been drafted by the previous tick, reviewed by Haytham, and departed overnight/this morning before this session started. Reconciled all 32 against Gmail reality via 4 parallel agents (8 leads each): 30 were the mechanical cold Touch 2→3 disambiguating-question closer, no reply on any thread, cold sequence complete → `Dormant`, `Next Action` bumped 2026-08-11 (confirmed non-Sunday). Two were NOT standard closes:
- **Rita Sanna** — cold Touch 1→2, carries `call-ask`: proposed "Wednesday morning or Thursday around 3." No reply yet. Stays `Outreach Sent`, `Next Action` 2026-08-03 (day 9).
- **Lucia Csobonyei** — warm Touch 5→6: she'd replied confused to the Touch 5 iheal finding ("I don't understand what are you referring to"); Haytham deleted the first redraft and sent a reframed Touch 6 that drops iheal entirely and closes with a call-ask (Thursday morning / Friday ~2pm). Stays `Reply Received`/Warm, `Next Action` 2026-07-30.

**Real bug found and fixed, not just a data problem.** Several of the 32 reconciliations initially FAILed `crm-gate log` with "no block for touch N" even though the touch was correctly logged. Root cause: `audit/crm_gate.py`'s `touch_blocks()` only ever recognized the legacy `[date] — Touch #N —` header — it was never updated for the `TOUCH: n=N dir=out ...` sentinel grammar that `touch-log render` produces and that `docs/uae-track/log-grammar.md` (2026-07-27) declares the only sanctioned way to write a line. Every lead logged with the new grammar was silently false-failing this gate. Fixed `touch_blocks()` to also count v2 touches via `audit.touchlog.parse_body` (local import, dodges a circular import — `touchlog` imports `parse_findings_bank` from `crm_gate`). Found a second, narrower bug while verifying the fix on Rita Sanna's real page: her legacy Touch #1 header had no trailing "Reply:"/"Next:" lines, so `touchlog.parse_body`'s legacy body-scan (which only stopped at another legacy header/heading/reply) swallowed the immediately-following v2 Touch #2 block whole. Fixed by also stopping the legacy scan at a `TOUCH:`/`OFFER:`/`SOURCE:` sentinel line. Both fixes verified against the actual affected Notion rows (not just synthetic tests) before and after; regression tests added (`tests/test_log_integrity_gate.py`, `tests/test_touchlog.py`); full suite green (322 passing). Commit `8603593`, pushed to `uae-track`.

**Minor follow-up, non-blocking:** several of the newly-inserted `TOUCH:` blocks (written by the reconciliation agents via Notion's `update_content`) carry a 3-backtick fence (```` ```javascript ```` ) instead of the log-grammar spec's literal 4-backtick fence. This means the sent body isn't attached to the parsed touch record (`body: None`) — `log-lint` reports this as a WARN ("empty body on a non-bounce touch"), never an ERROR, and it doesn't affect `crm-gate log`'s touch-count check (confirmed). Worth a cleanup pass re-inserting the correct 4-backtick fence on the affected rows, but not urgent.

**Top-of-funnel moved for the first time in 3 ticks:** after 07-25/26/27 all showing 0 `Sourced`/`Qualifying`/`Audit Ready`, this tick found 1 `Audit Ready` (Silvia Vladimirova, textalent.io — Finding Verified + Email Verified, no `Inbox` assigned yet, needs `haytham-hook-finder` before a draft can exist) and 1 `Qualifying` (Nedal Mohamadeiah, no email yet). Still thin, but not zero.

**Reply sweep:** clean beyond what's already logged — Christina Steinhoff's autoresponder resurfaced again (4th confirmed instance, no action), Lisa Hugo/Dina Taji/Rita Baki's 07-27 replies were all already fully reconciled with no new development.

**Ceilings:** Inbox 1 25/day (ramp step 2, day 7 — RAMP REMINDER: eligible for 30 if deliverability held, Haytham's call), Inbox 2 25/day (ramp step 2, day 4, next step eligible 2026-07-31). Today's sends: Inbox 1 17/25, Inbox 2 15/25 — both entirely the overnight batch above, no new opener headroom spent.

**Conversion ladder — still 0/9 replies converted to a booked call, but two live standing call-asks now exist for the first time**, both awaiting reply: Rita Sanna (Wed morning/Thu ~3pm) and Lucia Csobonyei (Thu morning/Fri ~2pm). Worth watching closely on the next tick.

**Hygiene:** clean sweep — no stale Asked For Price, no un-turn-two'd stale Reply Received, no Touch #0 on Outreach Sent, no cold Touch ≥4, no Sunday-landing Next Action. Notion SQL quota ran out partway through (as usual) right after the due-today query, before the future-dated-Last-Contacted check could run — deferred, same recurring limitation as prior ticks. Scoreboard not due (last partial computation was yesterday, 07-27).

### Open follow-ups
- [ ] Silvia Vladimirova needs `haytham-hook-finder` to get a hook + held draft — first fresh Audit Ready lead in 3 ticks.
- [ ] Cosmetic: re-fence the ~13-ish v2 `TOUCH:` blocks written this tick with 3 backticks instead of 4 (log-lint WARN only, not blocking).
- [ ] `Run source-leads`/`qualify-leads` — top-of-funnel is still thin (1 Audit Ready, 1 Qualifying) even after today's small movement.
- [ ] Watch Rita Sanna's and Lucia Csobonyei's threads next tick for a reply to their standing call-asks.

## 2026-07-27 — The opener is a cold read, not a finding (PR 4 of the First Five pivot)

**Findings stopped opening emails.** Every coach already wants more booked
calls, so a finding spends the whole email proving something she knows — and a
finding that turns out wrong, or that she fixes herself, costs more than
silence. Both already happened: 4 of 9 engaged leads consumed the finding and
left; a third of findings failed under scrutiny while carrying `Finding
Verified = YES`. Beat 2 is now a **cold read**: a measured observation true of
most coaches in this market. It cannot fail either way, because it makes no
claim about her specifically. Findings are RESERVED call bait and are never
emailed at any touch, in any form.

**The blocking discovery: the touch-1 path could not pass at all.** Once every
finding is `RESERVED`, three independent vetoes fired — `--opener-rank` was
required whenever a bank existed (enforced TWICE, at `main.py:342` and
`crm_gate.py:962`), any rank supplied was rejected for being RESERVED, and
touch-1 freshness drew `opener_finding()` which returns `None` on an
all-RESERVED bank. Confirmed by executing the gate before touching it. A
walked lead is all-RESERVED by definition now, so this would have blocked the
entire cold pipeline silently.

- **`--opener-rank` → `--cold-read <pattern>`**, at both layers. The old check
  existed because of a real incident (a draft built from page-body narrative
  instead of the bank, emailing the exact finding the bank was reserving). That
  incident is impossible now, but the declare-what-you-drafted discipline is
  kept and re-pointed at the sanctioned pattern list. Unlike `--opener-rank` it
  does not depend on the bank, so a row with no bank still declares its pattern.
- **H7 removed one day after it shipped.** It hard-failed a SHALLOW or untagged
  touch-1 opener. Its premise died with the finding-opener.
- **`second-finding` → `second-cold-read`.** A follow-up must carry a DIFFERENT
  pattern from the opener's. `second-finding`, `leak-fix-offer` and
  `loom-offer` all still pass as deprecated aliases.
- **Freshness now follows what the send actually draws on.** Touch 1 and the
  cold carriers cite no finding, so they get no ceiling. Warm touches still do
  — and that is where the Rita Baki incident actually lived (a warm Touch 5
  re-asserting a leak she had already fixed), so the protection that mattered
  is intact. Pinned by `test_warm_touch_still_checks_the_finding_it_stands_on`.
- **`reserved_deep_finding()` now returns the lowest-rank reserved entry**, not
  the first line. Harmless while exactly one was reserved; wrong now that a
  bank holds several.
- **`finding-verifier` re-pointed at the RESERVED entry.** It used to verify
  bank #1 and explicitly skip the reserve — i.e. certify the one finding that
  will never be used and ignore the only one that will.

**Two real bugs found and fixed in `uae-tick`,** both consequences of touch 1
no longer spending a finding: the confirmed-send `1. UNUSED → USED-T1` flip
would have recorded a spend that never happened, and the drift detector (an
`UNUSED` rank 1 on a sent row = "missed flip") **inverts** — it would have
false-alarmed on every sent lead in the CRM. Retired by name rather than
deleted.

**The numbers were audited before anything shipped, and four of seven had
problems:**
- **`46 of 122` is not shippable and is NOT in the pattern list.** It appears
  only in the offer spec, unsourced; the market study it names as its evidence
  base has no 46. The nearest real figure (32, free-call-only) is from the
  *disqualified* population — a different denominator. The `call-centric`
  pattern needs a fresh CRM count before it can exist.
- "373 reviewed in two weeks" → **"373 found in 14 days"** (246 were killed at
  triage without a walk; "reviewed" inflates sourcing into auditing).
- "122 sites this year" → **"about a hundred and twenty"** (the sanctioned
  wording in 8 places; and all repo activity is July 2026, so "this year"
  implies a year behind about three weeks of work).
- "four 5-star reviews over six months" → **"across the engagement"** (the
  site's own wording; only two are actually published, one for a one-day job).
- **`site/index.html:382` said "50% order bump take rate" while `:436` on the
  same page said "1 in 4 buyers."** My PR 3 journal claimed the site was
  reconciled — I had checked only one of the two lines. Fixed to 1 in 4.

Five cold-read patterns ship, each with its stat and source line:
`price-invisible` (48 of 122), `no-aed` (49 of 88), `price-band` (medians
1,831 / 894), `audience-decoupled` (18,400 off 268 followers), and
`rented-audience` (36 of 87) — the last written as a felt cost, never as a
missing mechanism, because the vitamin filter is unchanged.

**Also cleared, finally:** installed bs4, playwright, pytest and rich. The
PR 2 `data-url` capture and host dedup are now **runtime-verified**, not just
syntax-checked. And `test_calendar_state.py` used a `mp` fixture parameter
where every other file uses `monkeypatch` — **it had never run under pytest at
all.** Renamed; it now passes under both runners.

Tests **317, zero failures** — the first fully green suite of the session,
including the two files that had been unrunnable all day.

### Open follow-ups
- [ ] **Re-walk the rows queued to send before 07-30**, when the 219
      migration-stamped `verified:` entries expire. Warm touches still enforce
      the 3-day ceiling, so this bites live threads first.
- [ ] The `call-centric` cold read needs a real CRM count ("how many walked
      leads have a free discovery call as the only way in") before it ships.
- [ ] Existing walked rows carry `UNUSED`/`USED-Tn` statuses from before the
      change. They parse fine and nothing emails them, but a future walk should
      write everything `RESERVED`.

## 2026-07-27 — The old offer is retired and the close is a call ask (PR 3 of the First Five pivot)

The two jobs the pivot was actually about. **The funnel-fix offer is gone from
the repo, and every close is now a call ask with two specific times.**

**JOB 1 — retiring the offer.** The blocker was an authority claim:
`02-the-offer-gso-v2.md:3-4` said *"Supersedes all earlier pricing. If a number
anywhere else contradicts this, this wins."* A retired offer that still asserts
authority keeps winning arguments after it is dead, so the file was renamed to
`02-the-offer-first-five.md` and rewritten rather than deleted — the RETIRED
preamble now names everything that went and why.

- Retired everywhere: Track A (735), Track B / "The Booked-Out Funnel" (2,575),
  the 500 AED 48-Hour Leak Fix, the free Loom, the 3,600 next step, and the
  Live-or-Free / First Booking guarantees.
- **New guarantees: No-Show No-Charge + Five or Free.** The old two both
  promised funnel delivery ("live and taking bookings within 5 working days"),
  which The First Five does not do. The *discipline* is unchanged — both named,
  stacked, stated unprompted, condition intact.
- **New downsell ladder**, because the old rungs priced a build: fewer calls at
  the same rate → setup deferred at 750/call → the 1-10 check.
- **Code: add and deprecate, never delete.** `call-ask` is the canonical
  carrier; `leak-fix-offer` and `loom-offer` are both deprecated aliases that
  still pass with a note (the same machinery that already handled
  `loom-offer` → `leak-fix-offer`). `OFFER_TYPES` gains First Five / Fewer
  Calls / Setup Deferred and keeps the retired ones so `parse_body` can still
  read the 100+ OFFER: lines already in lead page bodies.
- **`EARNED_STATUSES` needed no new member.** `Call Booked` was already in it,
  and it is now *the* earned rung — the gate and the offer finally describe the
  same event. The Leak Fix statuses stay accepted as legacy.

**JOB 2 — the drafting overhaul.** The brief named two files. It was **ten**,
and the two named ones were not the load-bearing ones:

- The real blocker was `voice.md:19` — *"The email's job is to earn belief, not
  book a call"* — under a file that declares itself to outrank everything.
  Rewording only `gate.md:38` and `SKILL.md:228` would have left the doctrine
  above them intact and the model would have reverted on the next draft. Scoped
  it: belief still comes first and is what *earns* the ask; the ask is now a
  call. Kill list, register, burrito test, 10/10 bar untouched.
- **Five-beat body** replaces the four-line shape: hook → finding → **identity**
  → cost → call ask. 90-130 words. The beat order is the order her objections
  arrive in.
- **The identity beat is net-new** — no rule, gate check or skeleton slot
  existed. It had been firing *reactively at turn-two* to repair a misread that
  already happened (Amanda: *"I wasn't actually trying to book a chat"*). Two
  variants ship and both get tested: volume ("120 coaching sites this year") and
  outcome ("$522 from one order bump, about one buyer in four").
- **The finding demoted.** `mechanics.md:16` said *"Your opening email IS the
  lead magnet."* That sentence is what let 4 of 9 engaged leads read the
  finding, fix it, thank us and leave. It is evidence a human looked, not the
  product.
- **`mechanics.md:110` read as anti-evidence** ("Louise and Helen both stalled
  on vague scheduling asks"). It is about *vague* asks with no times and no
  price — reworded so it distinguishes itself from a dated ask instead of
  contradicting the new rule.
- **Take rate settled at 1 in 4** per Haytham. `mechanics.md:124`/`:137` and the
  offer doc said 1 in 2 / 50%; the public site and the new spec said 1 in 4. All
  now agree. The identity beat ships the number *without* the brand name.
- **Calendar URL promoted to `config.HAYTHAM_CALENDAR_URL`.** It lived only as
  literal text in a worked example, was wrong once, and shipped a fabricated
  `cal.com/haytham/15min` into real drafts (commit a6bf3a9).
- **"Loom Skeleton" → "Call Prep."** Nothing parses the heading, and the
  artifact is more useful than ever now that the call is the product.

**Gotcha:** the no-menu rule is written four times in this repo and the old
canonical turn-two script violated all four ("want me to fix it? … or here's my
calendar"). The new close can reintroduce exactly that if a calendar link gets
put beside the two times, so `gate.md` now checks for its absence explicitly.

Tests 313, unchanged count from PR 2 — six existing tests updated to the new
vocabulary (carrier aliases, guarantee names, offer types), none dropped.

Suite arithmetic for the whole pivot: 285 at session start → 290 (PR 1) → 313
(PR 2) → 313 (PR 3). The two non-passing files are pre-existing harness
artifacts, not logic: `test_evidence_promotion.py` imports pytest outright, and
one `test_inbox_routing.py` test needs a pytest fixture its bare runner can't
supply.

### Open follow-ups
- [ ] **The 07-30 send cliff is still open.** 219 entries on the
      `verified:2026-07-26` migration stamp expire for sends on 2026-07-30. Per
      Haytham's call, only rows actually queued to send get re-walked.
- [ ] Add `Unbooked calendar` to the Notion `Finding Type` select by hand, and
      note that `Est. Value` / `Discovery Anchor` options are now legacy buckets
      worded against retired prices (set `Est. Value = Unknown` on new rows).
- [ ] `examples.md` still carries the four question-closing UAE openers as the
      pattern to match. They are now the retired shape — a worked rewrite in the
      new five-beat form is the next thing that would help a drafter most.
- [ ] The six live warm threads still need re-pitching on the new offer. That is
      a human job, not a Claude Code one — a person is on the other end.

## 2026-07-27 — The finding taxonomy: calendar-state check, DEPTH enforced at the gate (PR 2 of the First Five pivot)

The opener stops being a funnel-mechanics defect. Under The First Five we sell
booked calls, so a finding the coach fixes in five minutes and walks away from
is worse than no finding — that is 4 of 9 engaged leads.

**The rule already existed and had quietly died.** `walk.md` added the depth
axis (SHALLOW/DEEP = self-fixability) on 07-26 and `SKILL.md:152` already ranked
depth-first. One day later the live CRM read: **203 of 225 bank entries with no
DEPTH tag, 8 of 91 leads with any DEEP finding, 8 with a RESERVED entry**, and
roughly a third of rank-1 openers still self-fixable. Exactly the "optional
fields die" failure the fix list predicts in §5. So this PR is enforcement, not
new doctrine.

- **`crm-gate send` hard-fails a touch-1 opener** drawing an untagged or SHALLOW
  bank entry (fix-list H7). Scoped to touch 1 — touch 2/3 are already bounded by
  `--carries`, and widening it would block every live follow-up.
- **`audit/calendar_state.py` + `main.py calendar-state`** — new. Reads the
  lead's PUBLIC booking availability with three unauthenticated `requests.get`
  calls. Verified live: Sadia Khan **271 open slots / 26 days** → `wide_open`,
  DEEP, opener-legal; Aleli Carissa 58 / 12 → `partial`, not a finding.
- **The calendar split.** `walk.md:44-46` listed "an empty calendar" as SHALLOW.
  That was two facts under one label. A scheduler publishing *zero* bookable
  time is a config bug she fixes herself → SHALLOW. A scheduler *working* with
  most of the month open is nobody booking her → DEEP, opener-legal. Only the
  second is an opener; a normally-busy calendar is not a finding at all and
  carries no depth tag, so it can't be banked as touch-2 material.
- **`verified:` is now stamped at walk time.** Both the CRM spec and
  `crm_gate.py` claimed it already was; the opener-finder never wrote it, so
  every freshly-walked row arrived already failing the freshness gate. Silvia
  Vladimirova did exactly that this morning. Three markdown edits, no code.
- **`Finding Type` gains `Unbooked calendar`** (needs adding by hand in the
  Notion UI — select options can't be created via API).
- **`refresh-finding` routes calendar findings to `calendar-state`** instead of
  the text diff. A Calendly page is a ~1KB JS shell, so the diff would read
  "unchanged" and auto-stamp a finding nobody re-checked.
- **The free win:** `_interactive_blind_spots` now captures `data-url` off
  inline booking widgets. That attribute is the lead's booking URL and was
  being discarded — the repo's documented screenshot blind spot is now this
  check's input. Also collapsed the 4th hand-maintained copy of the six
  scheduler hosts (`crawler._funnel_category`) onto `config.BOOKING_EMBED_HOSTS`.

**Gotcha that shaped the whole module.** A live Calendly call returned HTTP 400
with `failure.external_calendar_error` and no `days` key. A parser doing
`.get("days", [])` reads that as "this coach has no availability" — a fabricated
finding, which is the one thing this repo forbids outright. So status and
`failure` are checked before anything is counted, errors raise instead of
returning empty, and a verdict needs **2 consistent reads** (that same 400
cleared on 4 of 4 retries). `test_external_calendar_error_raises_never_reports_empty`
is the regression; if it ever passes by returning zero, the check is broken.

**The vitamin filter stays as written.** It bans a missing MECHANISM as an
opener ("you have no email capture"), which means the market study's 41%
no-email-capture figure is *not* promotable to an opener. An unbooked calendar
passes it because it is a felt cost, not a missing mechanism.

Tests: 290 → 313 (16 new for calendar-state, 6 for the depth gate and the
refresh-finding routing, 1 for the shallow-opener regression).
Two fixtures updated: `_TAGGED` in `test_findings_bank_depth.py` models the
pre-H7 shape (shallow opener) and now has a `_DEEP_FIRST` sibling for the
passing case, plus a regression pinning that a shallow opener no longer passes.

### Open follow-ups
- [ ] **`evidence.py` and `crawler.py` changes are NOT runtime-verified** — bs4
      is not installed in this container (same reason `test_evidence_promotion.py`
      fails). Syntax-checked and the regex logic tested standalone; the
      `data-url` capture needs a real walk to confirm.
- [ ] Add `Unbooked calendar` to the Notion `Finding Type` select by hand.
- [ ] TidyCal / Acuity / SavvyCal / YouCanBook.me return `unsupported`. TidyCal's
      routes need a network-capture pass; the other three are uninvestigated.
- [ ] ~55 of 91 live rows have no opener-legal finding banked. Per Haytham's
      call, only rows actually queued to send get re-walked. This also absorbs
      the 219 entries still on the `verified:2026-07-26` migration stamp, which
      expire for sends on **07-30**.
- [ ] PR 3 (retire the old offer + the drafting overhaul) still to come. Order
      bump take rate settled at **1 in 4**; `mechanics.md:124`, `:137` and
      `02-the-offer-gso-v2.md:187` still say 1 in 2 and get corrected there.

## 2026-07-27 — H3a: offer freshness ceiling dropped, unparseable-bank hole closed, 2 rows repaired (PR 1 of the First Five pivot)

First of three PRs for the UAE pivot to **The First Five** (AED 1,500 setup
credited against the first three calls, then AED 600 per call that happens;
spec in `docs/claude-docs/offer-the-first-five.md`). Shipped alone and first
because it was time-critical and independent of the offer rewrite.

**The brief's premise was stale, and it matters.** `fix-list-final.md` says *"no
lead carries a `verified:` tag, so every live row fails on its next send"* —
that was verified against `d772391`, before PR #86 and the 90-row backfill
landed on 07-26. Queried the live CRM: **all 91 live rows with a bank carry
tags.** The fix-list's evidence was `grep -rn "verified:20"` over the repo,
which structurally cannot see Notion, where lead rows actually live. Re-verify
that doc against HEAD before trusting its other P0 items.

The real problems, and what shipped:

- **`STALE_OFFER_DAYS` removed entirely** (`audit/crm_gate.py`). Its whole
  rationale was "a priced offer quotes work, the work must still need doing" —
  true when the offer was a 735/2,575 AED fix scoped around the finding. The
  First Five sells booked calls and quotes no work against the finding, so the
  1-day ceiling was blocking offers for a reason that no longer exists. It was
  also the near cliff: every migration-stamped row would have failed the offer
  gate from 07-28. Reversal-guard comment written where the constant used to be.
- **`STALE_SEND_DAYS = 3` untouched**, with the reason now written next to it.
  The finding is still cited in the opener as evidence the work was done, and
  citing a dead one is what Lisa and William both pushed back on.
- **The unparseable-bank hole is closed.** Both freshness blocks were guarded by
  a bare `if parse_findings_bank(...)`, so a bank with content that parsed to
  *nothing* was read as "legacy row, no bank" and **skipped the gate entirely** —
  strictly worse than a missing tag, which at least fails loudly. Rita's row was
  in exactly that state while carrying a live 3,200 AED quote. New
  `bank_is_unparseable()` + hard fail in `check_send`. A bank where SOME lines
  parse is deliberately NOT unparseable: leaving a killed finding in a
  non-matching grammar is the sanctioned way to hide it from the gate, and that
  had to keep working.
- **Tests 35 → 40.** Dead offer-ceiling tests replaced with ones pinning that
  there is no ceiling; Rita's real `DEAD`/`RETIRED` grammar added as a named
  fixture across four new cases. Suite otherwise unchanged (~285 pass; the two
  failures in `test_evidence_promotion.py` and `test_inbox_routing.py` are the
  pre-existing missing-`pytest` harness artifacts, not logic).

**Two rows repaired, not three.** The plan said three; on the full banks only two
were actually broken:
- **Rita Baki** — her rank 1 was tagged `USED-T1` and described as DEAD in prose,
  so the gate could still draw a finding she had already fixed herself. Demoted
  to the non-matching `DEAD (...)` grammar. Only her live rank 3 parses now.
- **Silvia Vladimirova** (Audit Ready, walked today) — three entries, no
  `verified:` tags. Stamped `2026-07-27`, which is honest: the walk was today.
- **Lucia Csobonyei was NOT broken.** Her `1. RETIRED |` line doesn't parse, but
  ranks 2-4 do — which is the mechanism working as designed, not a fault. The
  truncated first query made it look otherwise.

**Gotcha worth keeping:** the opener-finder does not stamp `verified:` at walk
time. Silvia was walked this morning and came out untagged, which is why a
brand-new row was already failing the gate. That is a walk-time bug, not a
backfill gap.

### Open follow-ups
- [ ] **219 of 225 live bank entries still read `verified:2026-07-26`, a
      migration stamp, not a real check.** They expire for SEND on **2026-07-30**
      (age 4). The offer cliff is gone; this one is not. A real `refresh-finding`
      pass needs per-finding page fetches and there are no stored baselines, so
      it is a real job, not a sweep — do it on the rows actually queued to send.
- [ ] Stamp `verified:` at walk time in `haytham-opener-finder` so new rows never
      arrive untagged (see gotcha above).
- [ ] PR 2 (finding taxonomy: openers move to client-acquisition state, calendar
      check) and PR 3 (retire the old offer, drafting overhaul) still to come.

## 2026-07-27 — Log discipline for the Notion → Airtable migration: touch-log grammar + parser, Notion schema additions, skills wired

Full implementation of the migration handover (PR 1-3; PR 4 backfill left
for a later, separate pass — see follow-ups). Wave 1 (122 leads) proved the
cost of the next migration is set entirely by how logs are written between
now and cutover: 40/243 sends (16%) missing from their logs and recovered
from Gmail, 8 permanently unrecoverable, reply type never data anywhere,
Gate 0 storing a verdict but not which floor fired. Goal: make the next
migration `parse_body()` in a loop, zero Claude-per-lead judgement.

- **`audit/touchlog.py` (new module)** — the `TOUCH:`/`OFFER:`/`SOURCE:`
  sentinel-line grammar: `render_touch`/`render_offer`/`render_source`
  (self-lint, fail closed — the only sanctioned way to write a line),
  `parse_body` (tolerant of the pre-2026-07-27 legacy prose format,
  verified against 5 real `docs/leads/<slug>/raw.md` archives including a
  6-touch multi-reply thread), `validate` (the full log-lint rule set:
  Touch # reconciliation, n contiguity, required tokens per direction,
  enums, Findings Bank/inbox cross-checks). Zero third-party deps,
  verified importable with playwright/PIL/bs4/requests blocked. Does not
  touch `crm_gate.py`/`send_cap.py`/`inboxes.py` or the Findings Bank DSL.
- **`main.py log-lint` + `touch-log render|offer|source`** — new commands.
  38 new tests in `tests/test_touchlog.py`, full suite still 286
  passed/8 skipped.
- **Notion schema — live, not just documented.** Added 6 additive
  properties to the UAE Lead CRM via `notion-update-data-source` (fetched
  the schema fresh first, confirmed no name collisions): `Gate 0 Failed
  Floors`, `Gate 1 Failed Reason`, `Disqualification Reason` (11-option
  taxonomy data-derived from `docs/leads/_dq-extraction.json`), `Hook
  Type`, `Hook Source URL`, `Last Reply Type`. Documented in
  `docs/uae-track/schema-delta.md` with every literal option string —
  Airtable can't create select options via API, so that file is the
  one-sitting checklist for Haytham to create them by hand before cutover.
- **Docs** — new `docs/uae-track/log-grammar.md` (standalone grammar
  reference, token tables, enums, Airtable field mapping); `01-crm-
  operating-spec.md` §2/§7 updated (new properties, new body template,
  prose sections untouched); one new CLAUDE.md hard rule (log at
  confirmation time via `touch-log`, `log-lint` must pass).
- **Skills wired, not just documented**: `haytham-email-draft` (UAE
  confirmed-send logging now emits `TOUCH:` via the CLI at confirmation
  time, runs `log-lint` alongside `crm-gate log`; parenting keeps its
  legacy format, out of migration scope), `uae-tick` (reply detection logs
  a classified `type`, sets `Last Reply Type`, new `log-lint --all`
  hygiene sweep over rows the tick already touched), `hook-verifier` +
  `haytham-hook-finder` (write `Hook Type`/`Hook Source URL` alongside the
  SMYKM line), `haytham-opener-finder` (Gate 0/1 fails + Lane 3 skips set
  the floor properties before Disqualified), `qualify-leads` +
  `qualifier-worker` + `qualifier-verifier` (same floor-record rule where
  most Gate 0 kills actually happen; verifier clears the fields on an
  overturned kill), `source-leads` + `sourcing-worker` (workers return the
  query string, orchestrator writes a `SOURCE:` line), `process-lead`
  (points at the grammar doc).
- Gotcha: the handover doc's `docs/leads/<slug>.raw.md` path was actually
  `docs/leads/<slug>/raw.md` — found while writing the legacy-parser
  tests; five real archives (rita-sanna, adam-ashcroft, sadia-khan,
  noona-nafousi, avneet-kohli) gave enough shape variety (single touch, no
  reply, multi-touch with real replies) to trust the tolerant parser
  without inventing fixtures.

### Open follow-ups
- [ ] PR 4 (backfill, optional/separate): parse `Hook Type`/`Hook Source
      URL` out of existing SMYKM Hook lines and a `SOURCE:` line where the
      sourcing journal has the query string, for the 122 already-migrated
      leads. Fix the one `Chetna Chakravarthy[` trailing-bracket name; leave
      parenthetical name suffixes alone (real disambiguators).
- [ ] Haytham: create the 6 new select/multi-select options in Airtable by
      hand from `docs/uae-track/schema-delta.md` — the API can't do it,
      and an unlisted option fails the cutover parse silently.
- [ ] Watch `log-lint --all` adoption over the next few ticks/batches —
      it should show a rising share of `format: "v2"` touches as skills
      actually use `touch-log render` instead of hand-typing.

## 2026-07-27 — uae-tick re-run (same day): Lisa Hugo's held closing draft went out, one more courteous reply, nothing else moved

Same-day re-run a few hours after the morning tick. Only one thing changed on Gmail: Haytham reviewed and sent the closing-reply draft this tick held for Lisa Hugo ("what platform are you running on") at 12:02 Dubai, and she replied again 2 minutes later — "We use GHL, white-labelled agency account, we run sub-accounts for clients." Logged as Touch #6; this is a courteous close-out, not a reopening of her decline, so Status stayed `Lost` and no further action was drafted. Full reply sweep (both inboxes, `after:2026/07/27`) turned up nothing else new — Christina's autoresponder resurfaced in the window (already handled this morning, no new action) and Dina Taji's thread showed no further reply. 🔥 Today view: all 31 rows show `Next Action = 2026-07-28` (tomorrow) — nothing due today. 📤 Send Queue: still 0 rows, top-of-funnel still completely dry. Notion SQL quota was still capped from this morning's run; fell back to the unfiltered view queries per the skill's documented workaround. Inbox headroom: Inbox 1 11/25, Inbox 2 16/25 (after Lisa's Touch 6).

## 2026-07-27 — uae-tick: 22-lead Gmail-state reconciliation (Haytham's whole 20-lead batch departed overnight), 2 real replies, top-of-funnel still bone dry

Scheduled daily tick, fresh session. The entire 20-lead follow-up batch drafted the previous session (13 cold Touch 3s + 7 warm/priced touches) had been scheduled by Haytham for Monday 2026-07-27 morning and had already departed by tick time (Inbox 1: 14 sends 05:00-07:01 UTC; Inbox 2: 8 sends ~05:00-06:00 UTC), plus 3 separate pre-existing `Scheduled` Touch-1 openers (Daphne Soares, Libby Salord McLean, Dina Taji, all Inbox 2) that were also queued for this exact morning. Reconciled all 22 rows against Gmail reality — fanned out 4 parallel reconciliation agents (mirroring the 07-25/07-26 precedent) for the 19 mechanical ones (no reply), handled the 3 with real inbound replies personally since they needed judgment calls. Every row passed `crm-gate log` on the first or second try.

**Mechanical (13 cold Touch 2→3, no reply → Dormant, 08-10 revival bump):** Shankar V Jayaraman, Susan Koruthu, Gayathri Murukan, Dr. Kim Dede, Lama Malaeb, Carol Glynn, Dr Larry Davies, Ghada B Khalifeh, Luca Allam, Saeed Alghafri, Bilna Sandeep, Noona Nafousi (+ Christina Steinhoff, see below). 5 of these carried a real cited third finding into the closer (bank flipped to USED-T3); the rest were the generic disambiguating-question line with nothing left UNUSED to spend.

**Mechanical (3 Scheduled Touch-1 openers → Outreach Sent/Reply Received):** Dr. Daphne Soares and Libby Salord McLean departed clean, no reply yet, bank #1 flipped USED-T1. Dina Taji (see below) is the one with a real reply.

**Mechanical (warm bumps, Touch #+1, Status unchanged):** Lee Harris (Price Discovery Sent, leak-fix-offer), William Brown and Lucia Csobonyei (Reply Received, both leak-fix-offers citing a fresh banked finding each — bank flipped to USED-T5), Avneet Kohli (Offer Sent, a non-pitch clarifying question about a Upwork brief she'd sent), Rita Baki (Offer Sent, the currency-fragmentation follow-up on her Notes-flagged re-scoped thread).

**The 3 replies, handled directly (not delegated):**
- **Christina Steinhoff** — the "reply" that landed 1 minute after Touch 3 is the SAME confirmed out-of-office autoresponder as Touch 1 and Touch 2 (identical wording, same `%...%` unfilled merge-tag subject, same ~1-min latency) — third confirmed instance. Reconciled as a normal cold-sequence-complete → Dormant, not a real reply. The account-safety WhatsApp-gate flag from 07-19 stands unchanged.
- **Lisa Hugo** — genuinely declined the 500 AED Leak Fix (Touch 5): "we have an expert on the team." She also disputed the cited finding (IG YouTube button 404) as not reproducing — the SECOND disputed finding on this lead after a real retraction on Touch 1, so bank #3 is now flagged DISPUTED rather than trusted. Set Status = Lost, Lost Reason = Not interested (only enum option available; full detail is in Notes). Drafted and held (not sent) a short non-pitching closing reply that picks up her "you never asked what platform we use" aside — Haytham's call whether to send it.
- **Dina Taji** — a real, warm, engaged reply on Touch 1 (same morning): she confirmed the pricing-mismatch finding is a known in-progress app relaunch, deactivating payments herself and expecting to launch in ~2 weeks. Not a decline, not a sale signal. Status → Reply Received, next check-in 2026-07-30.

**Conversion ladder:** still 0 replies converted to a Leak Fix sale or booked call, now against 9 unique repliers (was distinct from the historical, now-closed 100-lead price-discovery study). 3 Leak Fix pitches went out today (Lee Harris, William Brown, Lucia Csobonyei) with 0 accepted yet; Lisa Hugo explicitly declined. `crm-gate offer`: Avneet Kohli PASS (Discovery Anchor "Refused to name" — gate correctly reads this as a trust signal, recommends leading with guarantees, not a discount). **Rita Baki FAILs `crm-gate offer`** — bank #1 has no `verified:` freshness tag (predates the H3 gate), so the staleness check can't clear it; needs a `refresh-finding --rank 1` pass before her scope-mismatch flag can be trusted again. Not blocking anything today (informational, she's already Offer Sent) but worth doing before quoting her again.

**Attribution (9 unique repliers so far):** Lane is 100% Lane 1 (felt leak) — no Lane 2/3 repliers yet. Source Channel: Google Footprint 5, Coach Directory 2, LinkedIn 2. Finding Type: Other 2, Broken checkout 2, Weak sales page 2, Dead/stale element 1, Broken booking flow 1, No visible pricing 1 — too early to confirm or kill the old track's "Dead/stale element carries most replies" pattern; Google Footprint as a sourcing channel is the standout so far.

**Top-of-funnel is STILL completely dry** — `Sourced`/`Qualifying`/`Audit Ready`/`Draft Ready` all confirmed at 0 again (same as 07-26). Send queue empty; nothing to draft or send beyond the reconciliation above. The bottleneck remains findings, not sends.

**Hygiene:** clean sweep — no Sunday-landing Next Action dates, no cold Touch ≥ 4, no future-dated Last Contacted, no Outreach Sent with Touch # 0. Notion SQL quota (`notion-query-data-sources`) ran out mid-run (as usual) right after the attribution query, before I could re-check the carried-forward Spyros Bolano item (Dormant, Touch # null, bank #1 still UNUSED) or run the full log-integrity backstop sweep — both deferred again. One new gate-parsing gotcha found and fixed on William Brown's page: a historical "Touch #1 attempt #1 — Bounced" / "attempt #2 — Sent" pair doesn't match `crm-gate log`'s touch-block regex (it deliberately skips "attempt" blocks to ignore bounces) — reworded just that header line so the real send counts as Touch #1; no facts changed.

### Open follow-ups
- [ ] **Run `source-leads` / `qualify-leads` urgently** — top-of-funnel dry for a second tick running.
- [ ] Rita Baki — run `python main.py refresh-finding --rank 1` before her existing 3,200 AED offer scope is trusted again; `crm-gate offer` FAILs on the missing freshness tag as of today.
- [ ] Spyros Bolano — still unconfirmed (Dormant, Touch # null, bank #1 UNUSED) — Notion SQL quota ran out before this could be re-checked.
- [ ] Delete the stray orphaned Lee Harris Gmail draft and the duplicate Ben Pringle draft (carried over from 2026-07-26 — no delete-draft tool available this session).
- [ ] Lisa Hugo's held closing-reply draft (Inbox 2) — Haytham's call whether to send.
- [ ] Full log-integrity backstop sweep and Finding Type/Source Channel/Lane scoreboard splits beyond today's partial numbers — blocked on the Notion SQL quota again.

## 2026-07-27 — 20-lead follow-up batch drafted; wrong reference-doc calendar link + draft-update threading bug, both self-inflicted

Ran uae-tick's due-follow-up step across all 20 due leads (13 cold Touch 3s, 7 warm/priced
follow-ups), one drafting agent per lead in parallel. All 20 gated PASS and got a held Gmail draft.
Also fixed the `Findings Bank` formatting on Rita Baki (`DEAD` status → `USED-T1`/`RETIRED`, parser
now resolves `current_finding()` correctly) and Lisa Hugo (rank 2 was wrongly left `UNUSED` after
being sent as Touch 2 — flipped to `USED-T2` to match the actual Email Thread Log).

**Root cause, corrected after initially misdiagnosing it:** Haytham's real calendar link is
`https://calendly.com/haythamm/discovery`. The 4 `leak-fix-offer` drafts (Ben Pringle, William
Brown, Lucia Csobonyei, Lisa Hugo) all correctly used that link from the start. The actual bug was
`.claude/skills/haytham-email-draft/references/examples.md` carrying a DIFFERENT, wrong placeholder
link (`cal.com/haytham/15min`) as if it were a real sent example — when Ben Pringle's draft got
manually "corrected" against that reference, it broke the real link. Compounding it: a second pass
assumed the ORIGINAL `calendly.com/haythamm/discovery` link was the fabricated one and stripped it
from all 4 drafts entirely, before Haytham clarified it was correct all along. `examples.md` is now
fixed to the real link (2026-07-27) so this can't recur.

By the time the link URL was confirmed, Haytham had already independently fixed all 20 drafts by
hand in Gmail and scheduled them to send 2026-07-27 — so a second automated attempt to "restore"
the link mostly hit already-scheduled messages (no longer plain drafts, `update_draft`/`PUT
/drafts/{id}` correctly errored rather than corrupting them) and only left ONE unwanted side effect:
a stray duplicate Ben Pringle draft, created before checking that Haytham had already handled it
(and had deliberately chosen NOT to send that one — he moved the lead to `Dormant` instead). **Needs
deleting**, same as the Lee Harris orphan below. Lesson: check current Gmail state before any
corrective write, especially once a human has said "I already fixed it."

**Two Gmail-tooling gotchas surfaced along the way (still true regardless of the link mixup):**
- Using Gmail MCP's `update_draft` on an existing reply-draft (Ben Pringle, Lee Harris) silently
  **detaches it into a new orphaned thread** — the tool has no threading params, so re-editing a
  reply draft this way loses its attachment to the real conversation. Recover by recreating fresh via
  `create_draft` + `replyToMessageId` instead. Inbox 2 has no such risk (`gmail_gethaytham.py`'s raw
  `PUT /drafts/{id}` explicitly sets `threadId`/`In-Reply-To`).
  **Lesson: never use `update_draft` on an existing Inbox 1 reply-draft — recreate it instead.**
- Gmail MCP's `list_drafts` only returns `plaintextBody` for the single most-recently-touched draft
  in the whole mailbox; `get_thread`/`search_threads` never surface DRAFT-labeled messages at all —
  there is no safe way to bulk-read Inbox 1 draft bodies without touching (and risking) them.
- **Also confirmed: never trust an agent's self-reported "final copy" as proof of what actually
  landed in the Gmail draft/message object — read the object back directly.** This surfaced real
  drift between reported and actual content in this run and should stay standard practice.

### Open follow-ups
- [ ] Delete the stray orphaned Lee Harris draft (`r-8321922502352988444`, detached thread).
- [ ] Delete the stray duplicate Ben Pringle draft (`r-38787258041374869`) — he's going to `Dormant`,
      not being sent.
- [ ] Next uae-tick: reconcile these 19 scheduled sends against Gmail's `in:sent` once they actually
      depart — do the full confirmed-send logging checklist (Touch #, Last Contacted, Next Action,
      bank flip, Notes clear) only then, per the draft-is-not-a-send rule.

## 2026-07-26 — Pre-drafted Rita Baki's re-scoped quote (not sent, no reply yet)

Checked on the open follow-up: her Notion row is still `Offer Sent`, Touch 5, no reply. Nothing was
dropped — the TODO was conditional on her replying/booking, and that hasn't happened yet.
`rita-baki.raw.md:67` still carrying the original 3,200 AED copy verbatim is correct by design (R4's
never-edit archive rule), not a leftover bug.

Pre-drafted two variants through the full `haytham-email-draft` loop (voice, gate, critical-failures,
uae-track.md) so the re-scope is ready the moment she responds, since it shouldn't be worked out live
in the thread:

- **If she picks a call time** (likeliest, Touch 5 just asked): a short honesty note sent *before*
  the call, not on it, so it doesn't open with a pitch for a fix she's already made.
- **If she skips the call and asks for the number over email**: a real money email, 735 AED
  (Track A territory — remaining scope is one narrow fix, not the full Sprint), guarantee-equivalent
  stated in the same breath, single CTA. `crm-gate offer` wasn't run mechanically (`rich` isn't
  installed in this container) but both PASS conditions are independently true on her row (`Status
  = Offer Sent`, `Asked For Price = YES`).

Full copy:

> **Variant A (call-booked path):**
> Wednesday works.
>
> One thing before we get on, better said now than mid-call. I went back through your site to prep. That booking form is gone. A real Calendly scheduler is live in its place, working end to end. Good call on that.
>
> So the piece I quoted you around is already handled. What's left is smaller. Your pricing looks different depending on where someone lands. Dollars on your own site. Dirhams on the marketplace. Nothing on your other two listings. Still worth talking through, just at a different number than what I said before.
>
> Haytham

> **Variant B (email-ask path):**
> Straight answer since you asked for one. The piece I quoted you on, 3,200 AED, was scoped around your booking button. That's fixed now. The Calendly you set up is live and working.
>
> What's actually still costing you is smaller. Three different price tags depending on where someone lands on you. Dollars on your own site. Dirhams on the marketplace. Nothing on your other two listings. Cleaning that up so it's one true number everywhere runs 735 AED.
>
> Live and matching everywhere within 5 working days, or you don't pay. If a mismatch shows up again inside 30 days, I fix it free.
>
> Want me to start on it?
>
> Haytham

Neither was drafted into Gmail or logged to Notion — draft is not send, and there's no reply yet to
draft into. Whoever handles her actual reply should adapt the closer-fitting variant to what she
actually says rather than paste it verbatim (the bespoke check still applies). Supersedes the
"Rita Baki flag carried forward" reminder in the entry below (07-26 uae-tick) — the actual copy is
now ready, not just the reminder to re-scope.

### Open follow-ups
- [ ] Haytham / whoever handles Rita Baki's next reply: use Variant A or B above as the starting
      point, adapted to her actual wording, not pasted as-is.

## 2026-07-26 — Finding-staleness gate (H3): warm-touch fix, refresh-finding closes the loop, CRM backfilled

- Shipped the H3 finding-staleness gate (PR #83, `audit/crm_gate.py`): the
  Rita Baki case (her 3,200 AED offer was scoped around a booking-flow leak
  she'd already fixed herself) and Ben Pringle's dead thread were the same
  bug — a walk is a snapshot, threads run 5-10 days, and nothing re-checked
  a finding between the walk and the send/quote. `Findings Bank` entries
  now carry a `verified:YYYY-MM-DD` tag; `crm-gate send` hard-fails past 3
  days, `crm-gate offer` past 1 day, both naming the Rita Baki case in the
  failure message. A missing tag fails the same way an old date would.
- **Review caught two real gaps, both fixed same PR:** (1) the freshness
  check only reached touch 1/2/3 — `check_send`'s touch-range validation
  rejected anything past 3 outright, so WARM touches (Rita was on Touch 5,
  Avneet Kohli is on Touch 6) never reached it at all, which is the exact
  shape of the real incident. Fixed: only `touch < 1` is invalid now; every
  touch >= 2, cold or warm, runs the same follow-up gate. (2) a rolled
  touch-1 opener (queued past noon Dubai, scheduled for tomorrow) was
  checking freshness against TODAY instead of the day it actually leaves —
  a 3-day-old finding could pass today and turn 4-days-stale by tomorrow
  morning. Fixed: freshness now checks against the same `pause_day` the
  Sunday-pause check already computes.
- **`refresh-finding` now closes the loop instead of being a manual diff a
  human has to hand-edit the result of.** New `--url` fetches the finding's
  page live (plain HTTP GET + text extraction — cheap on purpose, not a
  full walk); when the re-fetch comes back UNCHANGED from the stored
  baseline it auto-stamps `verified:` to today and hands back the exact new
  `Findings Bank` property value, ready to write verbatim. A CHANGED page
  is never auto-stamped — a text diff can prove the page is different, it
  can't prove the specific finding is gone, so that case still needs a
  human read (or a fresh vision pass) before anyone bumps the date by hand.
  `--save-baseline-to` persists each run's fetch as the next run's
  baseline.
- **Backfilled the live CRM.** `verified:` is a brand-new field — before
  this, `grep -rn "verified:20"` matched exactly one place in the whole
  repo (the spec doc's own example), meaning every live lead would have
  hard-failed its very next send or offer gate check. Queried all 100 UAE
  CRM rows with a non-empty `Findings Bank`; backfilled `verified:2026-07-26`
  onto every entry on the 90 that aren't Disqualified/Lost (90/90 writes
  succeeded, nothing else on those pages touched — Status, Touch #, Notes
  all left alone). **This date is a migration stamp, not a real
  re-verification** — if you see a wave of ~90 leads all reading
  `verified:2026-07-26` in the CRM, that's why; it does not mean 90 findings
  were actually re-walked on 07-26, only that the gate went live that day
  and needed a non-blocking starting point. Real re-checks from here on
  should come from `refresh-finding`, not another bulk stamp.
  **Rita Baki's own row was a special case and is worth knowing about**: her
  `Findings Bank` used a bespoke `N. DEAD (...) | finding` annotation format
  (added during the 07-25 re-walk that first surfaced her fixed leak) that
  doesn't match the machine-parseable grammar at all (`STATUS` must be
  `UNUSED`/`USED-Tn`/`RESERVED`) — so her row was actually INVISIBLE to the
  new gate, the one lead the gate exists because of. Reformatted her rank 3
  (the one surviving finding) into canonical grammar with its real
  `verified:2026-07-25` date (the actual R6 re-walk date, not a backfill
  guess); ranks 1/2 (the two DEAD findings) are left as unparsed prose on
  purpose — they should never be drawn again, and not matching the grammar
  is exactly what keeps `next_unused_finding`/`current_finding` from ever
  selecting them.
### Open follow-ups
- [ ] Every subsequent send/offer on the 90 backfilled rows will read
      "verified N days ago" against the 07-26 migration stamp, not a real
      check — the first real `refresh-finding` run on each is still owed
      whenever its 3-day (send) or 1-day (offer) ceiling actually approaches.

## 2026-07-26 — Root-caused and closed the Email Thread Log drift (new `crm-gate log` gate)

- Root cause of the two prior recovery sessions (15 leads, then 24 leads,
  missing/incomplete Email Thread Log entries): confirmed-send logging is
  TWO separate Notion writes — an `update_content` append to the log, and a
  separate `update_properties` call that bumps `Touch #` and rewrites
  `Notes` — with nothing tying them together. On every one of the 24 rows
  the property write had landed (`Touch #` incremented, `Notes` said "Sent
  Touch N ... reconciled by uae-tick") while the log append silently
  hadn't. `Touch #` was claiming sends the page body couldn't back up for
  over a week before Haytham noticed by hand and asked for a Gmail
  recovery. Two shapes of the bug showed up: a touch missing entirely, and
  — worse — a LATER touch logged while an EARLIER one was missing (Touch #
  matched a naive block *count*, just not the actual sequence).
- **Fix: `audit/crm_gate.py` gets a third gate, `log`** (`check_log_integrity`
  / `touch_blocks` / `print_log_integrity`, wired as `python main.py
  crm-gate log <row.json> --page-body <body.md>`). It re-derives the touch
  history from the fetched page body itself by regex — never from a
  caller-supplied count, same trust model as every other gate here — and
  PASSes only when the log's touch blocks are EXACTLY `{1, ..., Touch #}`.
  A bounced attempt (`Touch #N attempt ... BOUNCED`) or a logged duplicate
  send doesn't count as the touch; the real send does. 12 new tests in
  `tests/test_log_integrity_gate.py`, including the exact "later touch
  present, earlier one missing" shape that a count-only check would miss.
- **Wired as a hard gate, not an optional check:** `haytham-email-draft`
  SKILL.md now requires re-fetching and running `crm-gate log` immediately
  after every confirmed-send write, on the SAME lead, before moving to the
  next one — FAIL means the send isn't logged yet, full stop, fix it now.
  `uae-tick` SKILL.md's step 0.5 (Gmail-state reconciliation, the exact
  code path that produced all 24 drifted rows) gets the same hard gate,
  plus a cheap backstop hygiene flag that targets rows whose `Notes` carry
  the `reconciled by uae-tick` / `confirmed against Gmail` batch-narrative
  language (the fingerprint of the original bug) instead of re-fetching
  the whole CRM's page bodies every tick. `pipeline-tick` gets the same
  backstop pointer — the gate is CRM-agnostic (only needs `Touch #` + page
  body), and parenting-track sends log through the same `haytham-email-draft`
  checklist.
- Both prior recovery sessions' 15 + 24 leads stay fixed (verbatim Gmail
  recoveries, not reconstructed); this closes the write path so the same
  class of drift can't silently recur and go unnoticed for a week again.

## 2026-07-26 — New hard rule: sends paused every Sunday (code-enforced)

- Added a code-enforced weekly send pause: no send leaves any inbox on
  Sunday (Dubai calendar day), cold or warm, on either track. Not a lower
  ceiling — zero for the day.
- Implementation: `audit/send_cap.py` gets `is_pause_day(day=None)`
  (Sunday check on the Dubai date) and `today()` now takes an optional
  `now` override so it composes with the existing cutoff/rolling logic
  used for testing. `audit/crm_gate.check_send` checks it FIRST, ahead of
  Finding Verified / Email Verified / ceiling / carrier checks, as a hard
  fail — a touch 1 opener checks the send-day it will actually leave on
  (post-noon-cutoff rolls to the next day), touch 2/3 and warm sends check
  today since they never roll.
- Documented in `CLAUDE.md` hard rules, and in `uae-tick` and
  `pipeline-tick` SKILL.md (both tracks share Inbox 1, so both needed the
  note — pipeline-tick doesn't call `crm-gate send` at all, so its copy is
  the only enforcement there; Haytham must hold Sunday sends by hand on
  that track).
- No CRM/Notion changes, no CLI flag changes — the gate just fails closed
  automatically on Sundays; skills already fetch-fresh and quote the
  gate's literal output line, so the FAIL message surfaces on its own.
- **Follow-up sweep (cadence, not just the send gate):** the gate covers
  sends, but nothing stopped a `Next Action`/revival-bump DATE from being
  computed onto a Sunday in the first place — a guaranteed one-day stall
  once it got there. Swept both live CRMs by SQL
  (`strftime('%w', "date:Next Action:start") = '0'`): found 14 UAE
  Dormant leads (Aina Raj, Navid Nazemian, Abdulla Mahmood, Gbemi Giwa,
  Doug Lambert, Nazia Khan, Andreea Zoia, Dr Joelle Samaha, Kim Araman,
  Sasha Quince, Ana Caragea, Maria Vitoratos, Siddharth Anantharam, Dr
  Katherine Iscoe) all sharing `Next Action = 2026-08-09` — a Sunday,
  because their 14-day revival bump was computed on 2026-07-26 (also a
  Sunday) and 14 is a multiple of 7. Bumped all 14 to **2026-08-10**
  (Monday). Parenting CRM: one hit (`April`, `Status = Lost`,
  `2026-07-05`) — terminal status, no live follow-up, left alone. No
  `Scheduled`-status row has a trackable date in Notion (that lives in
  Gmail's own schedule, not a CRM property) — out of reach for this sweep;
  worth a manual glance if a scheduled send is ever set for a Sunday.
- Closed the gap so it can't quietly recur: `haytham-email-draft`'s Next
  Action rule and the CRM operating spec's Dormant transition both now say
  to bump a Sunday-landing computed date to Monday, and `uae-tick`'s
  hygiene flags gained a standing Sunday-`Next Action` check with the
  exact SQL to re-run it.

## 2026-07-26 — uae-tick: 30-lead Gmail-state drift reconciled, pipeline top-of-funnel found completely dry

**The whole "Scheduled" bucket (33 rows) was stale against Gmail reality when this tick started.** Haytham had apparently sent through a full day's queued cold Touch 2/3 batch before this tick ran (all departed 05:00-07:00 UTC / 09:00-11:00 Dubai, ~2 hours before the tick started at 11:10 Dubai). Fanned out 4 parallel reconciliation agents (mirroring the 07-25 precedent) rather than doing it inline, each required to pull the real Gmail thread body before writing anything to Notion:
- **14 leads, cold Touch 2→3 (the final cold touch, cadence day 0/3/9):** Aina Raj, Navid Nazemian, Abdulla Mahmood, Gbemi Giwa, Doug Lambert, Nazia Khan, Andreea Zoia, Dr Joelle Samaha, Kim Araman, Sasha Quince, Ana Caragea, Maria Vitoratos, Siddharth Anantharam, Dr Katherine Iscoe — all flipped Scheduled → **Dormant**, Touch #3, Last Contacted 07-26, Next Action 08-09 (14-day revival bump). Notable: 5 of 14 (Joelle, Abdulla, Doug, Maria, Ana) carried a real third banked finding (bank #3 → USED-T3), not the generic disambiguating-question closer — only Aina (bank exhausted) and Andreea (bank never populated) got the generic "is this still on your radar?" line. The carry-something-new rule is being honored better than expected.
- **16 leads, cold Touch 1→2 (8 Inbox 1 + 8 Inbox 2), all carrying the leak-fix-offer pitch (500 AED, re-citing the original Touch-1 finding, no second finding spent):** Dr. Sheen Gurrib, Nikoleta Perinova, Szilvia Vitos, Eric Fit, Nadine Faddul, Jonny Parr, Caleb Jones, Dan Chadwick (Inbox 1); Daria Ibrulj, Zeina Karrit, Joel Arcus, Fatima Williams, Wardah Harharah, Ayo Nova, Mawada Alwazir, Andrew Nicholson (Inbox 2) — all flipped Scheduled → **Outreach Sent**, Touch #2, Last Contacted 07-26, Next Action 07-30.
- **3 leads genuinely still Scheduled** (Dr. Daphne Soares, Libby Salord McLean, Dina Taji, all Inbox 2) — real Gmail scheduled-sends queued by Haytham for Monday 2026-07-27 morning, left untouched.

Post-reconciliation counts: Outreach Sent 56→72, Dormant 10→24, Scheduled 33→3. Reply sweep both inboxes clean (no new replies since 07-25). Today's real send counts: **Inbox 1 = 22/25 (headroom 3)**, Inbox 2 = 8/25 (headroom 17, the 3 Monday-scheduled sends don't count against today).

**The bigger finding: the entire top-of-funnel is at zero.** `Sourced` = 0, `Qualifying` = 0, `Audit Ready` = 0, `Draft Ready` = 0 — every one of the 368 CRM rows is in Disqualified (246), a worked/terminal cold-sequence status, or a warm/priced stage. The Walk Queue and the Qualifying pile both went from "6 Qualifying" (per the 07-25 afternoon entry) to zero. Nothing is left to walk, qualify, or draft — once the current Outreach Sent/Dormant cohort finishes its cadence, sends stop entirely unless `source-leads` runs.

Conversion ladder: still 0/9 replies converted to a Leak Fix sale or booked call (unchanged from 07-24). Both Offer Sent rows (Avneet Kohli, Rita Baki) PASS `crm-gate offer`, informational only (already offered). **Rita Baki flag carried forward:** her pending 3,200 AED offer was scoped around a booking-flow leak she has since fixed herself — only the shallow currency-fragmentation finding still stands; confirm scope before quoting if she replies. Hygiene: one pre-existing bug spotted (not from today) — Spyros Bolano is Dormant with Touch # null and Findings Bank #1 still UNUSED, meaning his cold sequence's confirmed-send logging never ran historically. Full hygiene sweep and Finding Type/Source Channel scoreboard splits not completed — Notion's free-plan SQL query quota capped mid-run (same recurring limitation as 07-25).

### Open follow-ups
- [ ] **Run `source-leads` / `qualify-leads` urgently** — top-of-funnel is completely dry, zero rows in Sourced/Qualifying/Audit Ready/Draft Ready.
- [ ] Spyros Bolano (Dormant) — investigate why Touch # is null and Findings Bank #1 was never flipped; looks like a historical confirmed-send logging miss, not from this tick.
- [ ] Full hygiene sweep (bank-flip audit across all Outreach Sent/Dormant rows, 14-day ceiling history) and the scoreboard's Finding Type/Source Channel/Lane attribution splits — blocked on the Notion SQL quota this run, worth a follow-up once it resets.
- [ ] Watch William Brown and Lucia Csobonyei (Reply Received, Last Contacted 07-24 — hit the 2-day stale mark tomorrow if no further touch).

## 2026-07-25 — Disqualification reason extraction (Phase 3)

Read-only-Notion / write-repo-only extraction job over the 246 Disqualified UAE
rows (fresh count, not the assumed 246 — re-queried `Status = Disqualified`
via `notion-query-data-sources`, paginated 100/100/46 with `LIMIT/OFFSET`).
Output: `docs/leads/_dq-extraction.json`.

1. **Headline — the single biggest Gate 0 floor kill is "no funnel / no paid
   offer," 89 of 246 (36%), well ahead of #2 "not UAE-based" (34) and #3
   "has team/gatekeeper" (30, a Gate 1 fail but the next-largest bucket by
   volume). Audience-below-floor is 25, inactive-30d is 27.
2. **Sourcing implication:** more than a third of everything sourced turns out
   to have no purchasable product at all — corporate execs, B2B consultancies,
   Noomii/directory-only listings, DM-only or "book a free call" brochure
   sites with no visible pricing. The sourcing query is pulling "coach-shaped"
   people (title says coach, LinkedIn says coach) without confirming a
   checkout exists. Concrete fix: qualify-leads' Gate 0(b) check should run
   BEFORE the UAE/activity checks whenever a lead is found via title-only
   search (LinkedIn, Noomii, directories) — settle "is there a checkout"
   first since it kills more leads than every other floor, so a Gate 0(b)-first
   ordering saves the most wasted lookups per lead killed.
3. **Pass/Pass pattern (15 leads read individually):** these passed every
   gate and were killed anyway. The dominant pattern is NOT a funnel or fit
   problem — it's **undeliverable email** (6 of 15: Sahar Huneidi Palmer,
   Adil Hussain, Salma, Chiara Ghinolfi, Deema Ghata-Aura, Benjamin Owen —
   hard bounces, no public address, or enrichment HOLD on a non-branded
   domain). Second pattern is **duplicate/re-sourced-by-mistake** (4 of 15:
   Tanner Shuck, Dan Chadwick, Blooming Key, Bilna Sandeep — same lead
   already live elsewhere in the CRM, dedup missed it on a later sourcing
   pass). The remainder are one-offs: Lane 3 skip (Fadi Zouein, pivoted to
   music), 3 "Wrong fit" manual calls (Benish Mirza, Franda Graves, Joe
   Cotton — all IG/link-in-bio-only, no owned site despite passing the
   automated floors), and one hard evidence override (Faiz Alam — Trustpilot
   fraud allegations voided an otherwise-verified finding). Sourcing takeaway:
   Pass/Pass kills are an EMAIL problem and a DEDUP problem, not a targeting
   problem — the qualify gates are working correctly on this cohort.
4. **Out-of-order gate evaluation (Fail/Pass 21 + null/Fail 9 = 30 rows,
   re-derived fresh, matches the ~30 estimate):** yes, this is wasted
   qualification effort worth a process fix. These are rows where Gate 1 (or
   the "other" gate) got resolved before Gate 0 killed the row, or where a
   later re-check overturned an earlier verdict (e.g. Reim El Houni: Gate 0
   4/4 passed, promoted to Qualifying, THEN a re-check flipped Gate 1 on the
   same funnel). Every one of these represents a full second lookup that
   Gate-0-first sequencing would have skipped. Recommend `qualifier-worker`
   short-circuit on the first Gate 0 floor fail rather than resolving Gate 1
   in parallel.
5. **Taxonomy exposed a gap no CRM field currently holds:** "duplicate /
   re-sourced by mistake" and "no deliverable email" are both real, recurring
   kill reasons with zero representation in `Gate 0` / `Gate 1` (both are
   pass/pass cases) and only partial representation in `Lost Reason`. Without
   this extraction those 12 leads (6+6) look identical to a clean funnel/fit
   kill in every existing field.

Derived taxonomy (11 options, target 8-12; full definitions + per-lead
mapping in `docs/leads/_dq-extraction.json`):

| option | count |
|---|---|
| No funnel / no paid offer | 89 |
| Not UAE-based | 34 |
| Has team/gatekeeper | 30 |
| Inactive 30+ days | 27 |
| Audience below floor | 25 |
| Wrong fit | 15 |
| Lane 3 skip | 7 |
| Duplicate/re-sourced by mistake | 6 |
| No deliverable email | 6 |
| Manual judgement call by Haytham | 4 |
| Other | 1 |
| *(unmapped — note didn't clearly support any bucket)* | 2 |

Gate 0/Gate 1 matrix (fresh, 246 total): Fail/null=160, Pass/Fail=22,
Fail/Pass=21, Pass/Pass=15, Fail/Fail=13, null/Fail=9, Not checked/null=3,
null/null=2, Fail/Not checked=1 — matches the CLAUDE.md estimate closely.

Method: regex/keyword extraction over `Notes` text (avg 263 chars),
multi-select `gate_0_failed_floors` restricted to the 4 fixed floor strings,
single-select `disqualification_reason` derived from the actual text
(long-tail bucketed to "Other"), every mapping carries a verbatim
`evidence_quote` and a `confidence` (high/low/unmapped) — nothing guessed to
avoid an unmapped result. 244/246 = 99.2% mapped at high or low confidence;
2 genuinely unmapped left null rather than forced.

Acceptance checks: fresh count re-queried (246, not assumed) — done; ≥95%
mapped — done (99.2%); taxonomy 8-12 options with definitions and real
counts — done (11); Pass/Pass leads read individually — done (all 15);
every mapping has an evidence_quote — done for all high/low rows; no Notes
field modified anywhere — confirmed, Notion was read-only this session;
journal leads with the sourcing implication — done (see point 2 above).

### Open follow-ups
- [ ] Taxonomy needs Haytham's approval before it becomes an Airtable field
      (GATE 3) — this session has no Airtable access and did not create one.
- [ ] Per-lead `disqualification_reason` / `gate_0_failed_floors` data isn't
      applied anywhere yet — sits in `docs/leads/_dq-extraction.json` only,
      gated on Wave 2 (Airtable Team plan upgrade).
- [ ] Once Haytham approves the taxonomy, hand the option list + counts to
      the Airtable-side session so it can create the field there — do not
      create it from this session.

## 2026-07-25 — Synced R6's 3 dead findings into the live Notion CRM (Rita Baki x2, Ben Pringle x1)

R6 (previous entry below) caught 3 dead findings during the evidence-persistence re-walk, but that
sprint was read-only against Notion by design (coordination boundary with the concurrent Airtable
migration session). This left the actual live CRM — the thing `uae-tick`/drafting/replies read —
still showing those findings as live, on two active warm threads. Notion is still the source of
truth for pipeline state per CLAUDE.md, so fetched both pages fresh and wrote the correction
directly (`update_properties` + `update_content`, matched old_str against the live fetch, not the
repo doc, to survive Notion's markdown escaping):

- **Rita Baki** — `Findings Bank` property: Rank 1 (booking-form CTA) and Rank 2 (price-teaser)
  marked DEAD with the re-walk date; Rank 3 (currency fragmentation) is now the only standing
  finding. `Notes` + page body flag a real follow-on problem for Haytham: the 3,200 AED custom offer
  already pitched in Touch 4 was scoped around fixing the exact booking flow she's since fixed
  herself — if she books the call or replies, the price needs re-confirming against remaining scope,
  not re-quoted blind.
- **Ben Pringle** — Rank 1 (vanished Dubai Football Guide) marked DEAD in `Notes` + page body — the
  guide is back on the store. Flagged something sharper here: Touch #5, sent the same day the re-walk
  ran and still awaiting reply, already told him the guide "dropped off the store" — a claim the
  re-walk shows is no longer true. If he checks the store or disputes it on reply, the CRM now tells
  whoever handles that reply to acknowledge honestly rather than re-assert a dead finding.

Both leads' Notion pages now carry a `RE-WALK 2026-07-25` correction block and link back to the full
evidence trail in `docs/leads/<slug>.md`. Nothing else touched — no sends, no draft changes, no
status moves.

### Open follow-ups
- [ ] Whoever handles Ben Pringle's reply to Touch #5: if he pushes back on "the guide dropped off
      the store," don't re-assert it — the guide is back, acknowledge it.

## 2026-07-25 — Repo half of the Airtable migration: evidence persistence + 122 lead docs (R1-R6)

Worked the repo-side handover from the Airtable-migration session (docs/uae-track/ handover,
not yet committed as its own file — see this branch's commits). Six pieces, R1-R6, all shipped
to `claude/evidence-persistence-lead-docs-wrenyt`:

- **R1** — `.gitignore`'s `evidence/` rule was unanchored, so it also matched the promoted
  `docs/leads/<slug>/evidence/` folders (same name, different location) and silently ate the
  `!docs/leads/**/*.png` negation — a directory Git excludes can never have children re-included.
  Anchored to `/evidence/` (repo root only). Gotcha: `git check-ignore -v` reports exit 0 even for
  a NOT-ignored path whenever a negation pattern matches and prints — the real signal is
  `git check-ignore` (no `-v`) or `git status --ignored`, not the verbose exit code.
- **R2** — new `python main.py promote-evidence <slug> --kind finding|hook [--rank N] --source
  <path> [--force]` (`audit/evidence_promotion.py`): resizes to a 1600px longest edge, strips
  metadata, refuses to overwrite without `--force`. Pillow wasn't even installed in this
  container until this task — confirms why the lazy-import convention matters; `crm-gate`/
  `send-cap` verified working with `PIL` import blocked.
- **R3** — `docs/leads/_manifest.json`, the 122 non-Disqualified leads (`Status != Disqualified`
  in the UAE CRM), slugged via `audit.urls.slugify`. One real collision: two "Dan Chadwick" CRM
  rows, same name, same Site URL (beacons.ai/recruitmentguy) — looks like the same lead sourced
  twice, not two coaches sharing a name. Disambiguated with a page-id suffix
  (`dan-chadwick-c46c8a` / `dan-chadwick-643082`) since a domain fragment doesn't help when both
  rows point at the identical domain. Flagged for the Airtable session's reconciliation pass.
- **R4** — verbatim `docs/leads/<slug>.raw.md` archives of all 122 Notion page bodies, fanned out
  over 8 parallel background agents. Spot-checked one (Rita Baki) byte-for-byte against a fresh
  Notion fetch — exact match.
- **R5** — `docs/leads/<slug>.md` structured walk docs from the raw archives, same 8-way fan-out.
  Zero Email Thread Log / Price Discovery leakage across all 122 (grepped after every batch).
  One near-miss: an agent initially summarized a live reply inside a Findings block, caught it in
  self-review before finalizing — verified clean afterward. Several judgment calls on sparse Lane 2
  archives, retired/killed findings, and one case (Murielle Larrière) where a genuine walk
  correction was filed under the dropped `## Price Discovery` heading in Notion — kept the
  correction, dropped nothing price-related.
- **R6** — re-walked the 7 live/warm leads (Avneet Kohli, Rita Baki, Ben Pringle, William Brown,
  Lisa Hugo, Lucia Csobonyei, Lee Harris) live via Firecrawl, one per parallel agent, applying the
  honesty rule: promote evidence only for findings still visibly present today, mark the rest
  explicitly dead rather than silently reusing stale copy. **3 of the ~13 re-checked findings are
  now dead**, all fixed by the coach since the original walk — real, useful catches, not busywork:
  - **Rita Baki, Rank 1** — the actual finding her sent copy was built on. Her CTA no longer leads
    to a bare contact form; it's now a live Calendly scheduler. She fixed it. Do not reference
    this finding again with her (Offer Sent status — active thread).
  - **Rita Baki, Rank 2** — The Holistic Culture rebuilt her marketplace listing on a new platform;
    the price-teaser contradiction is gone (likely incidental to the migration, not a fix aimed at
    this).
  - **Ben Pringle, Rank 1** — the vanished £40 "Dubai Football Guide" is back on his Stan store.
  All other re-checked findings (Avneet Kohli #3/#4, William Brown #1, Lisa Hugo #1, Lucia
  Csobonyei #1, Lee Harris #1) held up unchanged and now have promoted screenshot evidence at
  `docs/leads/<slug>/evidence/`.

Never touched Airtable, never wrote to the Notion CRM (read-only throughout, per the handover's
hard boundary), never touched `crm_gate.py`/`dashboard.py`/`inboxes.py`/`send_cap.py` or any skill.

### Open follow-ups
- [ ] Airtable session: pick up `docs/leads/_manifest.json` (122 entries) to build Walk Doc /
      Evidence Path URLs; resolve the Dan Chadwick duplicate during reconciliation.
- [ ] Airtable session: set `Findings.Still Present = false` for Rita Baki Rank 1 + Rank 2 and Ben
      Pringle Rank 1 once those Airtable Findings rows exist. (Live Notion CRM already corrected —
      see the entry above this one.)
- [ ] A later pass backfills the `<!-- airtable-record: TBD -->` placeholders in all 122 walk docs
      once the Airtable session hands back a name → recordId manifest.

## 2026-07-25 — Ops: rebalanced Inbox 2's 07-28 send load (24 → 15)

Haytham flagged 07-28 as packed for Inbox 2. Queried the Pipeline Board
(SQL quota was capped, fell back to the unfiltered board view + in-memory
filter per the CLAUDE.md workaround) and found Inbox 2's near-term Next
Action load: 07-26 = 8, 07-27 = 4 (all warm Reply Received/Offer Sent
threads, untouched), **07-28 = 24** (cap 25), 07-29 = 2, 07-30 = empty.

07-28's 24 broke down as: 3 leads due Touch 2 (day-3 bump — Timothy
Fare-Matthews, Tracy Harmoush, Sam Fouladgar), 20 leads due Touch 3 (final
cold touch, bank #2 already spent per their Notes), and Rita Baki's live
Offer Sent thread (a warm reply awaiting response — never moved). No CRM
field encodes lead priority, so used two low-risk proxies instead of
guessing: (1) the 3 Touch-2 leads have the least sunk cost so far — moved
to 07-29; (2) among the 20 Touch-3 finalists, moved the 6 lowest-audience
(weakest reach signal) to 07-30 (Nick Carling, Dr. Corrie Block, Aman
Merchant, Sanjukta Ghosh, Kalyani Seth Soni, Suzanne Saleh). Rita Baki and
the other 14 Touch-3 leads stayed on 07-28.

**Result: 07-28 = 15, 07-29 = 5, 07-30 = 6 — all well under the 25 cap.**
Each moved row got a `Notes` append (preserving prior notes) documenting
the reschedule so `uae-tick` doesn't get confused and Haytham has
traceability. No sends, no drafts, no gate gets touched by this — just
`Next Action` dates. Next tick should treat 07-29/07-30 as normal send
days for these leads, counting them against Inbox 2's daily ceiling same
as anything else.

## 2026-07-25 — uae-tick (afternoon, part 2): 23 more departed follow-ups were sitting un-logged, likely a 🔥 Today view bug

Haytham flagged it directly: "CRM not synced, we have all departed follow-ups still have next action set to today." He was right, and the earlier same-day reconciliation entry (below, "1 more Gmail-state drift caught") undersold the scope — Rita Baki was one instance of a much bigger miss.

**What was actually wrong.** The 🔥 Today view (`39c382c8-4585-816e-bad3-000c4011b5df`) returned 31 rows, every single one with `Next Action = 2026-07-26` — not one row with `Next Action = 2026-07-25` (today), even though 23 real rows had exactly that. Pulling the unfiltered "All Leads" board (368 rows total, 4 pages) and filtering `Next Action <= 2026-07-25` in memory turned up 23 leads whose cold Touch 2 or Touch 3 had actually departed via Gmail this morning (all logged in Notes as "scheduled by Haytham to send 2026-07-25," i.e. queued by an earlier tick, then sent by hand) but whose CRM row still showed the pre-send Touch #, Last Contacted, and Next Action. **The 🔥 Today view itself looks miscalibrated — it appears to systematically exclude rows due exactly today** and only surface rows due tomorrow. This is worth Haytham checking directly in the Notion UI (view filter, most likely an off-by-one on the date comparison); until it's fixed, any tick that trusts that view alone for "what's due" will silently skip same-day departures the way this one did.

**The fix.** Built a reconciliation plan (23 leads, exact target Touch #/Status/Last Contacted/Next Action/Findings-Bank-flip/Notes computed up front from each row's own Notes text, which named the carrier and bank number for every send) and fanned it out to 4 parallel agents, each required to independently confirm the actual Gmail send (subject + body + SENT date) before writing anything to Notion — no CRM write without a confirmed departure. All 23 reconciled:
- **15 cold Touch 1→2** (Bonge Gumede, Nabil El Fquir, Samira Alexander, Nikki Evans, Sabeen Javed, Caroline Bakker, Kalyani Seth Soni, Sanjukta Ghosh, Aleli Carissa Gimena, Dr. Jamila Al Hosani, Dr. Corrie Block, Asma Ahmad, Sadia Khan, Trisha Hazarika, Monika Singh) — Touch # → 2, Last Contacted → 07-25, Next Action → 07-28, Email Thread Log appended with the real sent copy. 13 of 15 carried a second banked finding (flipped `UNUSED` → `USED-T2`); Nabil and Caroline Bakker carried Loom-offer only (single-finding rows, nothing to flip).
- **8 cold Touch 2→3** (Danielle Smith, Monica Wadwa, Bettina Koster, Jasmin Manke, Kelly Lynch, Elizaveta/Elle, Susan Fulignati, Shelley Bosworth) — Touch # → 3, **Status → Dormant** (3-touch cold sequence complete, never a Touch 4), Next Action → 08-08 (revival check), Email Thread Log appended.

**Two things the agents caught that my own batch instructions got wrong** (both self-corrected against the precomputed plan file, which was the actual source of truth): Trisha Hazarika is on Inbox 2/gethaytham, not Inbox 1/gmail-mcp as I'd told that agent; and Nikki Evans's real sent subject ("who'd hire a 25 year old coach") didn't match what her old Notes implied — the agent used the real Gmail header instead of guessing. Spot-checked Kalyani Seth Soni and Trisha Hazarika's pages afterward: both clean, bank flips correct, log entries correctly anchored (several pages had an empty Email Thread Log section with no prior "Next:" line to anchor on — agents correctly anchored on the literal `## Email Thread Log` / `## Price Discovery` adjacency instead of guessing a line that didn't exist).

**Open follow-up:** the 🔥 Today view's filter needs a human look in Notion — until then, any tick should double-check against an unfiltered board pull rather than trusting 🔥 Today alone for same-day departures.

## 2026-07-25 — uae-tick (afternoon re-run): 1 more Gmail-state drift caught, otherwise unchanged

Second UAE tick of the day (13:30 Dubai), Notion SQL query quota already exhausted from the morning run so this pass leaned on view-mode reads (🔥 Today, 📤 Send Queue, 💸 Asked For Price) and Gmail-native counts. Nothing due today changed since the morning brief: 📤 Send Queue still 0 rows (bottleneck is findings, not sends), the 🔥 Today view's 31 rows are all `Next Action = 2026-07-26` (nothing due yet), reply sweep (`in:inbox after:2026/07/24` both inboxes) still clean.

**Caught one more Gmail/CRM drift: Rita Baki's warm-bump reply departed between the two ticks.** The morning entry noted her Touch-5 nudge was drafted and "held for Haytham's review/send" — by this afternoon it had actually gone out (Inbox 2, thread `19f74c5bc42664c9`, departed 2026-07-25 09:14 UTC / 13:14 Dubai, ~15 minutes before this tick started) but the CRM still showed the stale "held" note and Touch #4/Last Contacted 07-21. Fixed: Touch # → 5, Last Contacted → 2026-07-25, Next Action → 2026-07-28, Notes rewritten to drop the "held" language, Email Thread Log appended with the sent copy verbatim. No bank flip needed (warm bump carried no new finding). Avneet Kohli's parallel warm bump (already logged in the morning entry) checked out fine against Gmail, no further drift there.

Conversion ladder: both 💸 Asked For Price rows (Avneet, Rita) already had their warm bumps out — nothing new to draft. Ceilings unchanged from the morning read (Inbox 1 25/day step 2 day 4, Inbox 2 25/day step 2 day 1, no ramp reminder). Scoreboard not due (last run 07-19, needs 7+ days). Nothing else moved — pipeline is quiet for real until the walk queue produces a fresh Audit Ready lead.

## 2026-07-25 — uae-tick: Gmail-state reconciliation catches 7 drifted rows, reply sweep clean, send queue empty

Ceilings: Inbox 1 25/day (ramp step 2, day 4), Inbox 2 25/day (ramp step 2, day 1) — no ramp reminder yet, both hold until 07-28/07-31. Sent so far today: Inbox 1 = 18/25 (headroom 7), Inbox 2 = 12/25 (headroom 13).

**Step 0.5 reconciliation was the real work this run.** All 4 `Scheduled` rows (Sam Fouladgar, Rita Sanna, Timothy Fare-Matthews, Tracy Harmoush — Touch 1 openers) had already departed via Gmail's own scheduled-send; flipped each to `Outreach Sent` with the full checklist (Touch #1, Last Contacted, Next Action +3, Findings Bank #1 → USED-T1, Notes cleared, Email Thread Log appended). Separately caught 3 more rows whose CRM state had drifted behind Gmail reality even though they weren't `Scheduled`: **Avneet Kohli** (Touch # already showed 5 but her day-3 warm bump had also departed today — bumped to Touch 6), **Ben Pringle** (Notes still read "held as a draft, not yet sent" for his answer to "What do you want mate?" — it had already sent this morning, Touch 5), **Lisa Hugo** (same pattern, warm bump already sent, Touch 4). None of these would have surfaced without checking actual Gmail thread state against the CRM's claimed state — the CRM's own notes were stale in all three cases.

**Gotcha:** the Gmail MCP's `search_threads` truncates the `messages` array within a thread (relevance-based, not chronological) — Ben Pringle's thread showed only 5 of 7 messages on the first pull, hiding both his 07-23 reply and today's departed answer. Had to re-pull all 18 Inbox 1 "sent today" threads via `get_thread` (full content) to get an accurate per-thread message count for the ceiling math. `gmail-gethaytham search` similarly caps at ~10 threads by default — trust `python main.py inbox counts` (paginated `/messages` list, not thread search) for the real count, not a manual search tally.

**Rita Baki caught stale two ticks running.** `Asked For Price` + Last Contacted 07-21 (4 days) — flagged 07-24 too, and the "warm bump draft queued, held for review" note from that tick was false: no draft existed anywhere in the mailbox. Drafted the day-3+ nudge now (fresh slot this week, WhatsApp offered, no re-pitch of price/guarantee) since this is the second consecutive tick flagging the same gap.

Reply sweep: clean, no new replies either inbox since 07-24. Conversion ladder: no fresh Reply-Received leads due a turn-two; Avneet Kohli and Rita Baki both `crm-gate offer` PASS (already Offer Sent, informational only). Send queue: **0 rows in Audit Ready or Draft Ready** — the walk queue (6 Qualifying) hasn't produced a fresh Audit Ready lead in a few days; bottleneck is findings, not sends. Scoreboard not due (last run 07-19, needs 7+ days, only 6 elapsed).

Notion hit its free-plan hourly SQL query cap partway through (a few queries in) — fell back to view-mode queries (🔥 Today, 💸 Asked For Price) for the rest, which cost against a separate quota. A full-table hygiene sweep (Touch#=0 on Outreach Sent, cold rows at Touch≥4, un-flipped bank entries, 14-day ceiling history) wasn't completed this run because of the cap — worth a follow-up once the SQL quota resets.

## 2026-07-24 — Price discovery is falsified. The track re-gates on earned right.

**The finding, plainly.** The UAE track was built on one hypothesis: that
asking a coach what they'd pay, before quoting, would explain why cold leads
don't close. After 100 touched leads, 182 touches and 9 replies, the question
was asked 3 times and produced 3 answers, all `Refused to name`, and 0 numbers.
Two of the three refusers responded by asking us for a price instead. The
refusal is a trust signal, not a price signal. The question moves to the call;
the gate moves to "have you earned the right to name a number." **The real
constraint was never price — it is reply → call, which is 0/9.**

This is a real result. It just isn't the one the track was hoping for.

**What the gate blocked in practice.** Not Avneet and Rita, as first assumed —
both were already `Offer Sent` with `Refused to name` anchors, so they passed
the old gate. The leads actually blocked were the four warm ones with nothing
logged at all: Ben Pringle, William Brown, Lisa Hugo, Lucia Csobonyei, all
`Reply Received` with a null `Price Discovery Answer`. Those are now unblocked
the moment they earn it.

**Code (`audit/crm_gate.py`, `main.py`).** `check_offer` now PASSes on either
of two routes: an earned `Status` (`Call Booked`, `Leak Fix Sold`, `Leak Fix
Delivered`, `Offer Sent`, `Won` — Status is a single select and forward
progress overwrites, so has-been-there counts) or the new `Asked For Price`
checkbox. `Price Discovery Answer` / `Discovery Anchor` are demoted to
advisory and reported as notes; a `Refused to name` anchor emits a WARNING
note saying it is a trust signal and the email should lead harder with the
guarantees. `check_offer` now returns a 3-tuple `(ok, problems, notes)` to
match `check_send` (only caller was `print_offer`). **The 500 AED turn-two
Leak Fix is explicitly exempt from this gate** — it is the rung that earns the
right, so gating it would deadlock the motion. 18 new tests in
`tests/test_offer_gate_earned.py` (there were zero on `check_offer` before);
`check_send` untouched, full suite 197/197.

**Carrier rename.** `CARRIERS` is now `second-finding | leak-fix-offer |
disambiguating-question`, with `DEPRECATED_CARRIERS = {"loom-offer":
"leak-fix-offer"}` and a `normalize_carrier()` helper. `--carries loom-offer`
still PASSes (in-flight rows, queued follow-ups, journal history) and appends
a deprecation note; failure messages advertise canonical names only. The
deprecation note is appended LAST so the carrier note stays `notes[0]`, which
`tests/test_send_gate_dubai.py` asserts positionally.

**Offer rebuild (three changes, price held).**
1. **The 48-Hour Leak Fix, 500 AED paid after** (365 AED up front incl. the
   12-point teardown) replaces the free Loom at turn-two. The Loom was offered
   to Ben Pringle, Lisa Hugo and Lucia Csobonyei and taken by none — high
   effort for the prospect, low dream outcome. New statuses `Leak Fix Sold` /
   `Leak Fix Delivered` give a paying customer somewhere to sit.
2. **Track B becomes a named stack:** "The Booked-Out Funnel — 5-Day Sprint
   for UAE Coaches", 10,000 AED of components for 2,575 AED, plus three named
   bonuses and honest scarcity (2 builds/week growth-rate cap).
3. **Two named guarantees, stacked and unprompted:** Live-or-Free (live and
   taking bookings within 5 working days or you don't pay and keep the work)
   and First Booking (no booking in 30 days and I keep working free, condition:
   you send traffic). There was previously no guarantee anywhere in Track B.
   Plus a standing named downsell ladder (payment plan 1,300+1,275 → "The
   Minimum" 1,800 → the 1-10 check).

⚠️ **The price did NOT move. 2,575 AED holds.** 3,600 is documented in
`02-the-offer-gso-v2.md` as the next step, gated on 2 closes. Zero closes have
landed; changing the price and the offer at once destroys the read.

**Notion (applied live).** Status +`Leak Fix Sold` +`Leak Fix Delivered` (all
15 prior options preserved); `Est. Value` +`Leak Fix (500 AED)` +`Sprint (2575
AED)` +`Funnel Watch (600/mo)` — **note: no comma, Notion rejects commas in
select option names**; new `Asked For Price` checkbox and `Cash Collected`
number. Two new views: 💸 Asked For Price (`3a7382c8-4585-81be-9b04-000c02607c46`)
and 🎯 Constraint Board (`3a7382c8-4585-8145-9a6c-000c59480cf2`, grouped by
Status over the reply→call stretch). Price Discovery Study renamed to
"(concluded)" and kept, not deleted. `Asked For Price` checked on Avneet Kohli
and Rita Baki, both of whom explicitly asked for a costing and both of whom
were 3-4 days stale — exactly the failure the new view exists to prevent.

**Docs re-pointed** so no file still asserts the old rule: `CLAUDE.md`,
`get-started.md`, `01-crm-operating-spec.md` (lifecycle, transition table, new
queries, page-body template now has a `## Money` section), `04-the-outreach-method.md`
(STANDARD MOTION steps 5-8 + a new `## WHAT IS NOW PROVEN` section carrying the
falsification), `pipeline.html` (stage 07 "Reply & convert"), `uae-tick`
(the discovery ladder is now the **conversion ladder**; new hygiene flags for
stale `Asked For Price` and un-turn-two'd replies; scoreboard tracks the
constraint), the whole `haytham-email-draft` reference set, and
`audit/dashboard.py`'s `STATUS_ORDER` (the new statuses would otherwise have
fallen into the unknown-status bucket).

**Open follow-ups.**
- Nothing has been sold yet. UAE 4 in `examples.md` is a composite reference
  draft, not a sent receipt — replace it with the real thread once one runs.
- The four blocked warm leads (Ben Pringle, William Brown, Lisa Hugo, Lucia
  Csobonyei) are owed a turn-two carrying the Leak Fix.
- `Price Discovery Sent` rows still exist and are now worked as
  `Reply Received`.

## 2026-07-24 — Dev: close a real bait-and-reserve enforcement gap (Tracy Harmoush incident)

Same-day follow-on to the finding-depth tiers commit below. Ran qualify-leads →
batch-audit → haytham-hook-finder on 3 fresh Qualifying rows (Rita Sanna,
Timothy Fare-Matthews, Tracy Harmoush). Two of three drafted clean; **Tracy
Harmoush's Touch 1 draft was built from the page-body "strongest verified
finding" narrative instead of the Findings Bank's rank order, and ended up
emailing the exact `$1` broken-promo-code finding the bank had correctly
tagged `RESERVED | DEEP`** — the deep call-bait finding that's supposed to
stay off-email entirely. `crm-gate send` printed a clean PASS because nothing
in it cross-checked the drafted content against the bank; the bait-and-reserve
check only ever emitted an informational note ("deep finding held in
reserve"), never a hard fail, and had no way to know the note didn't match
what actually went in the email.

**Fix (`audit/crm_gate.py`):** new `opener_finding(row)` helper (the
lowest-ranked `UNUSED` bank entry — the only thing a touch 1 email may be
built from). `check_send` gains `--opener-rank`, required for touch 1
whenever the Findings Bank is populated: hard-fails if the declared rank is
`RESERVED`, doesn't match the true bank #1, or is missing. Legacy rows with
no bank stay ungated. Wired through `main.py`'s CLI. 6 new regression tests
in `tests/test_findings_bank_depth.py` (15/15 pass; full suite 170/170).
Updated `haytham-hook-finder/SKILL.md` and
`haytham-email-draft/references/uae-track.md` to say explicitly: read the
Findings Bank property, not the page-body narrative, when picking what a
touch 1 opener carries — the two can and did disagree.

**Manual cleanup still owed:** Tracy's flawed Gmail draft (message
`19f9436b39f9ec92`, Inbox 2/gethaytham.com transport) has no delete API on
that path — needs deleting/unscheduling by hand in Gmail before send-day
07-25. The corrected draft (message `19f946a99da85891`, opens on the real
bank #1 terms-link-404 finding) is the one to send instead.

## 2026-07-24 — Dev: finding-depth tiers + bait-and-reserve (P1) + warm-reply craft (P2)

Branch `claude/finding-depth-tiers-jydpvw`. Two linked problems: (1) upstream —
openers led with the most falsifiable finding, which is almost always the most
trivial/self-fixable one, so leads read the opener, fixed the small thing free
(Rita booking redirect, Avneet test-SKU+logo, Lisa "on fix this"), and had no
reason left to pay; (2) downstream — warm replies reverted to opener/pitch
machinery (a five-word "What do you want mate?" drew a four-paragraph pitch).

**Problem 1 (finding depth):**
- **New depth axis** (orthogonal to Tier A/B/C severity) in
  `haytham-opener-finder/references/walk.md`: SHALLOW/self-fixable (janitorial —
  dead links, test SKUs, forms that should be schedulers, wrong logos) vs
  DEEP/un-self-fixable (pricing architecture, no owned audience, product-value
  leakage), with concrete deep examples pulled from the funnel-auditor diagnosis
  matrices + the real leads. Key rule: **depth is independent of provability.**
- **Ranking flip:** opener-finder SKILL.md now ranks **depth-first (deep over
  shallow), then tier, then sting** (was "tier first, then sting"). "Most
  falsifiable" is no longer "best."
- **Bait-and-reserve with CODE TEETH:** the `Findings Bank` line format gained a
  backward-compatible optional depth token + a new `RESERVED` status
  (`N. STATUS | DEPTH | finding`). `audit/crm_gate.py`: `_BANK_LINE` regex
  extended, `parse_findings_bank` carries `depth`, new `reserved_deep_finding()`
  helper, `next_unused_finding` now provably never draws a RESERVED entry (the
  deep call-bait can't be spent as a second-finding), and `check_send` emits a
  reserve note / low-value WARNING (never a hard fail). Legacy `N. STATUS |
  finding` rows still parse identically — verified.
- **Free-value cap extended to DEPTH:** shallow findings namable freely, a deep
  finding's fix/diagnosis is call-only (name it exists + costs her, never the
  how); RESERVED deep finding never emailed. New hard rule in mechanics.md +
  gate.md.
- Format spec mirrored in all 3 defs (crm_gate docstring, schema.md,
  01-crm-operating-spec.md) — drift-grepped clean. Agent contracts
  (lead-processor return JSON gains `deep_reserved` + `low_value`;
  finding-verifier gets a report-only reserve check) + process-lead/batch-audit
  wording updated.

**Problem 2 (warm replies):**
- Dense **"Warm replies (the turn-two craft)"** section added to mechanics.md
  (was 1 line): core "match the reply, answer, one step, stop" + good/bad pairs
  for all 5 reply types (blunt, brush-off, price question, logistics, five-Q
  deflection).
- **Reinforcement-loop / new-payload rule rescoped to COLD only** (mechanics.md
  line 17 was the leak); warm counter-rule made explicit.
- New critical-failure entry **"Warm reply written as an opener/pitch"** (the
  "What do you want mate?" anti-pattern).
- **Small-deal closing** block (Track A / sub-$1k): answer price directly, the
  "range" = the two tracks (735 AED floor / 2,575 AED ceiling, each flat — no
  within-track range, no change to "price never moves"), standing risk-reversal
  on every quote, WhatsApp switch (esp. UAE), stop after the ask. Matching
  gate.md boxes.

**Decisions locked in (defaults, offered but not overridden):** price "range" =
the two tracks (preserves every fixed-price hard rule); reserve got code teeth;
low-value flag is lightweight (Notes + body + gate note, no Notion schema
change). **Note for review:** a deep finding at bank #2 CAN still be emailed as
a second-finding (named as cost, fix withheld) — only the RESERVED one is held
entirely; that's intended (deep second-finding = the felt-cost teaser).

Tests: new `tests/test_findings_bank_depth.py` (8) + legacy send-gate (9) +
email-verify (16) all green. `rich` isn't installed in this container so
`main.py` CLI can't import; exercised `crm_gate.print_send` directly instead.

## 2026-07-24 — uae-tick: 26 due follow-up drafts (17 Inbox1 + 9 Inbox2), reply sweep clean, send queue dry

Ran the daily uae-tick after a 3-day gap (last tick 07-21; no journaled ops
07-22/07-23). Found a concurrent session had already worked several warm
threads minutes before this tick started (Lee Harris price-discovery
reply, Donna Brown explicit decline, William Brown + Lucia Csobonyei warm
bumps, plus 6 new leads walked to Outreach Sent — Suzanne Saleh, Nick
Carling, Marie Hondekyn, Michele Barouki, Josh McCartney). Verified each
against fresh Gmail/Notion state before proceeding so nothing got
double-drafted.

- **Reply sweep (both inboxes, since 07-21): clean.** No new unhandled
  replies — Donna Brown's decline and Lee Harris's non-reply were already
  reconciled by the earlier session; Rita Baki's thread unchanged
  (awaiting her Wed/Thu call pick, not yet due).
- **26 due follow-up drafts created, all gated where the cold sequence
  applies:**
  - **15 cold Touch 2** (day-3 bump, `crm-gate send --touch 2` PASS):
    13 carried `second-finding` (an UNUSED bank #2 existed); **Nabil El
    Fquir** and **Caroline Bakker** had no second bank entry, so gated
    `loom-offer` instead — exactly the case the gate exists to catch.
  - **8 cold Touch 3** (day-9, final cold touch, `crm-gate send --touch 3`
    PASS, `disambiguating-question`, no bank on any of the 8): Danielle
    Smith, Monica Wadwa, Bettina Koster, Jasmin Manke, Kelly Lynch,
    Elizaveta, Susan Fulignati, Shelley Bosworth — each closes "should I
    stop following up, or is this still on your radar."
  - **3 warm bumps** (no numeric gate, per skill — cold gate only covers
    touch 1-3): Ben Pringle (Inbox 1), Lisa Hugo + Avneet Kohli (Inbox 2,
    the latter nudging past-due Wed/Thu call times on her custom Retainer
    quote).
  - Inbox 1 totals today: 1 already sent (Lee Harris) + 17 queued = 18,
    well under the 25 cap. Inbox 2: 2 already sent (William Brown, Lucia)
    + 9 queued = 11, under the 20 cap.
- **Discovery ladder: empty.** No `Reply Received` row was both warm and
  past its turn-two with no discovery question asked yet — the live warm
  threads (Lisa, William, Ben) haven't re-engaged past their Loom offers,
  so asking discovery now would be asking into a stall.
- **Send queue (Touch 1 openers): empty.** Audit Ready / Draft Ready both
  at zero — confirms the 07-21 note that the bottleneck is walks/hooks,
  not sends. Today's batch-audit run fed Outreach Sent leads, not fresh
  Audit Ready ones, since all 6 newly-walked leads got Touch 1 same-day.
- **Ramp reminder: Inbox 2 (20/day) has held 8 days** — eligible for the
  25/day step if deliverability held. Did not run `send-cap set` (never
  automatic); surfaced for Haytham's call.
- No new bounces/spam flags in either inbox's sweep window — nothing
  appended to `deliverability-log.md` this run.
- Scoreboard not due (last run ~07-19/20, needs 7+ days).

**Bug found (Haytham, same day): the reply sweep missed a real reply.**
Ben Pringle replied 2026-07-23 16:08 UTC ("What do you want mate?",
`INBOX` label, well inside the `after:2026/07/21` sweep window) but
`mcp__Gmail__search_threads` (both a plain query and an exact-phrase
quote) returned his thread WITHOUT that message — it stopped at his
07-21 Touch 4 send. `mcp__Gmail__get_thread` on the same thread ID
returned it fine. Root cause looks like a search-index lag on that MCP
tool, not a query-syntax problem (in:inbox after:date worked correctly
for messages from 07-22 same sweep). **Fix for next time: when a warm
thread stays quiet past its expected reply window, re-verify with
get_thread on the known thread ID before assuming genuine silence —
don't trust search_threads alone for a lead that matters.** Drafted the
generic "just floating this back up" bump on top of an unseen reply,
which read badly against his actual message; Haytham deleted it.
Corrected: logged his reply verbatim on the page, drafted a real answer
(what Haytham does + the Dubai Football Guide finding + re-offered Loom),
held as a draft, not sent.

**Correction (Haytham, same day):** the uniform `Next Action: 2026-07-25`
across the due list wasn't a formula quirk, it was deliberate — he shifted
all Next Action dates +2 days CRM-wide to match the real 2-day gap since
the 07-22 work (no tick ran 07-22/07-23; today was the catch-up/prep day).
**These 26 drafts go out tomorrow (07-25), not today** — send/schedule
them then, and split Inbox 1's 17 into two sittings (pacing cap is 10 per
inbox per sitting; well under the 25 cap in total, but still worth
spreading). Next session: a `Next Action` a day or two past a batch's
natural cadence is not automatically staleness — check for a deliberate
shift like this before assuming a missed tick.

### Open follow-ups
- [ ] Send/schedule the 26 drafts tomorrow (07-25), Inbox 1 split across
      two sittings.
- [ ] Watch Lee Harris's price discovery answer (question sent 07-22, no
      reply yet); log verbatim + anchor the moment it lands.
- [ ] Avneet Kohli: her Tue/Wed call offer has lapsed twice now: if
      today's nudge also goes unanswered, next tick should treat this as
      a stalling signal, not another bare bump.
- [ ] Inbox 2 ramp: Haytham's call on 20 -> 25/day.

## 2026-07-21 — Wafa Bassili: turn-two sent, declined, marked Lost

Drafted and worked her full turn-two arc after this morning's uae-tick
flagged her thin Touch-1 reply ("Thanks for flagging. Noted") for a
value-add follow-up rather than a straight push to price discovery.

- Drafted two variants (haytham-email-draft skill): one spending bank #2
  (the pre-form CTA garble) as the reason to offer a walkthrough, one a
  bare Loom offer. User picked the bank-#2 variant, then flagged the
  "I help coaches grow" line — the first pass ("I go through pages...")
  read as hobbyist leak-hunting instead of an outcome. Rewrote to lead
  with growth/no-tech-worry before the ask.
- Created the Gmail draft directly in Inbox 2 (gethaytham.com, direct
  API path), correctly threaded as a reply to her Touch-1 message.
  User confirmed send.
- Logged the confirmed send: Touch # → 2, Findings Bank #2 flipped
  USED-T2, Notes/Email Thread Log updated (Status stayed Reply Received
  — a Loom offer isn't a stage transition until it's actually recorded
  and delivered).
- **She replied within the hour, verbatim: "thank you for flagging the
  typo. I didn't request a website review. Leave it there."** — an
  explicit decline, not a stall. Marked **Lost / Not interested**, Next
  Action cleared, Email Thread Log closed out with her exact words.
  Correctly did not default to "Dormant" here — that status is for a
  cold thread going quiet, not an explicit no on a warm one.

## 2026-07-21 — uae-tick: reconciled a 19-lead Scheduled batch (1 bounce), Rita Baki offer-ready, pipeline dry

Ran the daily uae-tick. The bulk of the work was reconciliation: a prior
session's draft-first hook+draft batch had scheduled 19 Touch-1 sends that
all departed 05:00-07:00 Dubai this morning with none of it reflected in
the CRM yet.

- **Reconciled all 19 Scheduled rows** (3 parallel subagents on the
  mechanical 17 + 2 handled directly for their extra wrinkles):
  - 17 clean Touch-1 sends → Outreach Sent, full checklist (Touch #,
    dates, Findings Bank #1 flipped USED-T1, Notes cleaned, Email Thread
    Log entries): Daria Ibrulj, Szilvia Vitos, Nadine Faddul, Joel Arcus,
    Eric Fit, Dr. Sheen Gurrib, Fatima Williams, Lee Harris, Zeina Karrit,
    Wardah Harharah, Dan Chadwick, Caleb Jones, Nikoleta Perinova, Ayo
    Nova, Mawada Alwazir, Jonny Parr, Andrew Nicholson (9 Inbox 1 + 8
    Inbox 2).
  - **Wafa Bassili** sent + replied 9 minutes later ("Thanks for
    flagging. Noted") → Reply Received/Warm directly, skipping a
    plain Outreach Sent stop. Thin reply — flagged for a value-add
    follow-up (turn-two artifact) rather than pushing to discovery.
  - **Sam Fouladgar hard-bounced** (Recipient Unknown) despite the
    07-20 WARN override materializing as a real bounce. Reverted to
    Qualifying, Email Verified unchecked, bounce logged to
    `docs/deliverability-log.md`. Needs a fresh address before any
    resend.
- Also reconciled two Touch-2 follow-ups that departed today (**Rima
  Zanoun**, **Salma El Shurafa** — both carried their bank #2 finding,
  both gate PASS) and **Ben Pringle's** Touch 4 warm bump (Loom offer
  on the vanished-guide finding, still no reply).
- **Rita Baki replied** to the Touch 3 + Loom + price-discovery combo
  send: *"Thanks, makes sense. we are on it. Tell me how you work on
  bookings, packages, tiers, rates?"* — deflected the anchor question
  back at our rates instead of naming a number. Logged verbatim,
  `Discovery Anchor: Refused to name`, `crm-gate offer` PASS. Ready for
  the money email on Haytham's go-ahead.
- **Send-day 07-21 load, cap 20/inbox:** Inbox 1 = 10 (all Touch-1 +
  Ben's bump), Inbox 2 = 12 (8 Touch-1 + 2 Touch-2 + Sam's bounced
  attempt). Both well under cap.
- **Inbox 1 hit its 7-day ramp-eligibility mark today** (20/day since
  07-14) but `deliverability-log.md` shows 3 hard bounces on Inbox 1 in
  that same window (Chiara/Adil 07-16, Neha 07-17) — flagged the tension
  in the brief rather than just parroting the ramp reminder. Inbox 2 not
  eligible until 07-23.
- **Pipeline is dry at the top: Audit Ready / Draft Ready / Scheduled
  are all at zero** (confirmed across all 360 CRM rows via a background
  count sweep — Notion's SQL query tool hit its hourly free-plan limit
  mid-tick, worked around via view-mode queries + a background agent).
  Walk Queue has no live Gate0/1-passed candidates; Qualifying/Sourced
  sits at only 9 raw rows. Bottleneck has moved from walks/hooks to
  sourcing — matches the 07-20 note that the market is drying up.
  `source-leads` top-up is the next move before batch-audit has anything
  to work.
- Scoreboard not due (last run 07-19, needs 7+ days).

## 2026-07-21 — Ops: Rita Baki — Loom delivered, price discovery dodged, custom 3,200 AED offer sent
Worked Rita Baki's warm thread through two more touches by hand (haytham-email-draft skill), off the back of her 07-20 yes to the Loom. Continues where the uae-tick entry above left off (her Touch #3 reply and dodge) through the Touch #4 offer send.

- **Touch #3 (Inbox 2, 07-20):** delivered the recorded Loom walkthrough plus the price discovery question in the same email (combined rather than split into two touches — a deliberate deviation from the skill's default "let the artifact land first" sequencing, Haytham's call). Cleaned two em-dashes and a near-miss on the "quick question" kill-list phrase out of his draft.
- **Her reply (07-21, verbatim): "Thanks, makes sense. we are on it. Tell me how you work on bookings, packages, tiers, rates?"** — she dodged the discovery question entirely and asked for our rates instead. Logged per the track's own rule: a dodge is data, not a second chance to ask. **Discovery Anchor = Refused to name.**
- **Gotcha, worth remembering:** when I re-fetched her Notion page to log that reply, the page **already** showed the answer, anchor, and a "crm-gate offer: PASS" note in the body — the concurrent uae-tick session above had already reconciled it. Did not trust the note at face value. Re-ran `python main.py crm-gate offer` myself on a fresh dump and got the same PASS independently before proceeding. Never treat a claimed PASS sitting in a CRM note as the real gate result — only a literal script run counts, exactly per the hard rule; this is the scenario that rule exists for.
- **Touch #4 (Inbox 2, 07-21): custom-scoped offer, 3,200 AED, off-catalog.** Haytham wrote a full-booking-system-rebuild offer at 3,200 AED, which is neither Track A (735) nor Track B (2,575) — flagged this explicitly against the "the price never moves" hard rule before drafting anything. **Confirmed intentional** (AskUserQuestion): the scope (end-to-end booking rebuild across her own site + marketplace) is genuinely bigger than either documented track, so this is a new custom/Retainer-tier quote, not a discount or a drift. Logged `Est. Value → Retainer` with the 3,200 AED figure flagged in Notes since it isn't a catalog number. Added the unprompted guarantee his draft was missing ("if it's not live and working when you check it, you don't owe me for it") and broke up two three-item comma lists that read as a tricolon.
- **Status: Price Discovery Sent → Offer Sent.** Findings #2 and #3 left `UNUSED` — the offer email referenced the cross-platform pricing split only as loose scope color, judged as not "spending" a bank entry the way a cold-touch carrier does. Flagged this as a judgment call Haytham can override.
- Closed with two named real call times (Wed 2pm / Thu 11am Dubai) instead of asking if she wanted to schedule — his explicit instruction, tied to a lesson from a different playbook (avoid the open-ended "want to hop on a call?" ask).
### Open follow-ups
- [ ] Watch for Rita's pick between Wed 2pm / Thu 11am Dubai — first reply moves her to Call Booked.
- [ ] If she doesn't reply by 07-24 (Next Action), warm-cadence check-in; findings #2/#3 still banked/UNUSED for a future touch if needed.

## 2026-07-21 — Qualifying run: 8 Sourced → 2 Qualifying, 1 Disqualified, 5 held

APIFY_TOKEN not set — all gates resolved via Firecrawl only. Workers' writes
didn't land (CRM unchanged post-agent), so orchestrator applied them directly.

- **2 promoted → Qualifying (both verifier-CONFIRMED):**
  - Timothy Fare-Matthews — 10.1K IG (Firecrawl snippet), Skool $3,800/yr, Dubai,
    active 29m ago. Business coach.
  - Tracy Harmoush — 692K IG (Firecrawl snippet), Playbook app $14.99/mo, Dubai,
    Arab Woman Award 2020. Fitness coach.
- **1 Disqualified (verifier-CONFIRMED):** Priya (Living liife) — Skilldeer-only
  listing, three separate passes found zero matching social profiles. Genuinely
  no measurable audience.
- **5 held Sourced/Not checked:** Reim El Houni, Rita Sanna, Haya AlDoserri,
  Coach Bethany, Coach Marios. All pass the other floors; audience (and
  activity for some) blocked behind IG/LinkedIn/YT login walls. Need APIFY_TOKEN
  to resolve.
- Walk Queue: 3 (Timothy, Tracy, + Sam Fouladgar held pending new email).

## 2026-07-20 — UAE top-up sourcing: market genuinely drying, 5 logged vs 15-20 target

Ran `source-leads` at top-up volume via the shared orchestration chassis (4
sourcing-worker waves + a sourcing-verifier pass), starting from only 3 rows
at `Sourced` (well under the 40+ stop threshold). Result: **5 new `Sourced`
rows**, not the usual 15-20 — every vein independently reported "drying."

- **Google Footprint (default channel), rotated to the stalest platform x
  geo combos:** Systeme x Abu Dhabi (stale since 07-13) + Teachable x
  Sharjah, then Kajabi x Sharjah + Skool x Sharjah (Sharjah had literally
  zero footprint rows ever — the least-worked geo in the CRM). Sharjah
  returned nothing new for any platform; Systeme x Abu Dhabi's subdomain
  query was pure noise (escort/jet-charter/cruise spam). Broadening Kajabi
  and Skool to plain UAE surfaced 2 genuinely new candidates before hitting
  a wall of ~355-row CRM dedups and non-UAE coaches merely mentioning
  Dubai. Combined: 3 candidates (Haya AlDoserri/Teachable, Reim El
  Houni/Kajabi, Timothy Fare-Matthews/Skool, 72-member audience confirmed).
- **Fallback 1 — ICF Directory** (stalest channel by last-Created, only 5
  rows ever, untouched since 07-16): thin by nature for this ICP — ICF UAE
  is dominated by corporate/bespoke executive coaches who sell via
  discovery call, not a self-serve funnel. 2 candidates (Rita Sanna
  cleared; Dr. Vanessa Moussa dropped by the verifier — real ICF Dubai
  coach but the offer is entirely call-gated, no visible price/checkout,
  so it failed the "real purchasable offer" bar).
- **Fallback 2 — Podcasts/Events:** 9 searches, mostly international
  speakers, unresolvable IG reels, and already-CRM'd big UAE names. 1
  candidate (Tracy Harmoush, Playbook fitness-app membership).
- **sourcing-verifier** re-fetched all 6 merged candidates independently:
  cleared 5, dropped Dr. Vanessa Moussa (call-gated, no offer). Haya
  AlDoserri kept with City = Unconfirmed (UAE-vs-Bahrain residence
  unresolved — past employment in both, AUS grad, surname reads Bahraini;
  flagged for `qualify-leads` to settle, not a plain non-UAE miss).
- **Wrote 5 rows to the UAE Lead CRM as `Sourced`** (batched
  `notion-create-pages`): Haya AlDoserri, Reim El Houni, Timothy
  Fare-Matthews (audience 72), Rita Sanna, Tracy Harmoush. CRM now holds
  ~8 at `Sourced` (3 pre-existing + 5 new) — still well under the 40+ cap,
  needs another top-up soon.
- **The honest read:** this is the finite-market signal the sourcing
  discipline warns about, not a bad run — 3 independent veins (footprint,
  ICF, podcasts/events) all converged on the same "mined out" conclusion
  against the CRM's 355-row history. Next top-up should try link-in-bio
  footprint or LinkedIn (both under-worked relative to Coach Directory/
  Google Footprint's saturation) rather than re-hitting these three.
- **Next step, unchanged:** `qualify-leads` (Gate 0 + Gate 1) needs to run
  over the `Sourced` pile before any of this reaches the Walk Queue.

## 2026-07-20 — Re-checked the 3 remaining unconfirmed Sourced leads

After the apify.py error-surfacing fix, went back through the other 3
leads that stayed `Sourced`/unconfirmed out of today's qualify run (Coach
Marios/Coach Bethany were the apify-bug ones, covered separately) —
resolved 2 of 3:

- **Andrew Nicholson → `Qualifying`.** His IG handle was wrong the whole
  run: `@padelperformanceclub` is an unrelated clothing brand. Scraped his
  own site's outbound links and found the real handle,
  `padel_performance_program` — 8,873 followers, posting daily, bio matches
  his coaching exactly. Audience floor clears comfortably.
- **Dr. Marjan Dorkhan → `Disqualified` (activity, now a confirmed fail
  not a guess).** Found her LinkedIn (1,690 followers, clears the audience
  floor she was originally killed for) but her own posting history shows a
  genuine 30-day activity fail: last personal post 5 months ago, everything
  recent is her day-job dental clinic's company page. This replaces the
  earlier "Not checked" with a real, resolved verdict — she's a
  recheck-later candidate since it's an activity-only fail, not niche/geo.
- **Priya (Living liife) — stays `Sourced`, still genuinely unresolved.**
  Second search pass for her real name (Priyanka) + NLP/theta-healing/Dubai
  only surfaced unrelated Priyas (Priya Singh, Priya Jain — different
  studios). No site or social linked from her Skilldeer listing. Correctly
  left unconfirmed rather than guessed.

Net effect on the Walk Queue: 11 rows at `Qualifying` now (was 10).

## 2026-07-20 — Fix: apify ig details silently swallowed actor errors

Root-caused the "apify ig misrouting" note from today's qualify run.
**Not** a `--mode` routing bug — verified `--mode details` correctly hits
`apify~instagram-profile-scraper` (real followersCount reproduced on a known
handle). The real bug: when that actor can't resolve an account (private,
renamed, nonexistent), it returns a per-item `{"error": "not_found",
"errorDescription": "Post does not exist"}` instead of a non-2xx HTTP
response — `_lean()`'s field allow-list in `audit/apify.py` doesn't include
`error`/`errorDescription`, so the failure silently vanished, leaving what
looked like an empty-but-valid profile (`{"username":..., "url":...}`)
instead of a visible failure. That confusing shape is what read as a
routing bug to the qualifier-verifier.

Fix: `audit/apify.py` — new `_raise_on_actor_error()` checks dataset items
for an `error` field before leaning and raises a clear `ApifyError`
("actor could not resolve X: <reason> — likely private/renamed/nonexistent,
not a code/routing issue") instead of silently stripping it. Wired into
both `instagram()` branches (`details` and `posts`). `--raw` still bypasses
it (raw callers see the full actor response either way). Verified against
a known-good handle (`@instagram`, real follower count) for no regression,
and against `coachmariosdxb`/`coachbethan` (now raise clearly instead of
returning an empty-looking success).

Re-checked the two leads this blocked: tried several handle variants for
both (Coach Marios: `coach.marios.dxb`, `coach_marios_dxb`; Coach Bethany:
`coachbethany`, which resolved to an unrelated US football coach, not her)
— genuinely unresolvable via any available tool (Firecrawl can't reach
instagram.com at all, Google no longer indexes IG profile snippets). Their
CRM Notes updated to record this precisely so it doesn't get re-litigated
as a "tool bug" next time. Both correctly stay `Sourced`/Not checked per
the qualify-leads skill (never guess an unresolvable floor into a Fail).

## 2026-07-20 — Qualify run: 10 promoted to Walk Queue, 3 killed, 5 held unconfirmed

Ran `qualify-leads` over the 18 fresh `Sourced` rows from today's top-up (chassis-
compliant): 2 `qualifier-worker`s gated 9 rows each (Gate 0 → Gate 1, resolving
audience with LinkedIn/IG/YouTube actor calls where Firecrawl couldn't read a
count), then a `qualifier-verifier` re-checked every promotion and every kill in
a fresh context.

- **Promoted to `Qualifying` (10, all verifier-CONFIRMED):** Wardah Harharah,
  Sam Fouladgar, Tanner Shuck, Dan Chadwick, Caleb Jones, Nikoleta Perinova,
  Moza Alfardh (1,951 — close to the 1,500 floor, held up), Ayo Nova, Mawada
  Alwazir, Jonny Parr. Two SERP-snippet audience numbers the verifier flagged
  for re-check (Tanner Shuck, Dan Chadwick) both reproduced via direct actor
  call — Tanner's was actually understated (266K SERP vs 353,965 actual).
- **Disqualified (3, verifier-CONFIRMED):** Coach El (6 Skool members, hard
  audience fail), Mohammad Elsaghir (0 LinkedIn posts in 30 days, Skilldeer
  page dead since 2021), Stefano Fichera (647 on LinkedIn, largest channel,
  below floor).
- **Verifier overturned 1 kill:** Dr. Marjan Dorkhan — a worker had failed her
  on "no owned audience channel," but that's an unresolved floor, not a seen
  sub-1,500 number; the skill is explicit that unresolvable stays
  `Sourced`/`Not checked`, never a guessed `Disqualified` (a hard Disqualify
  never gets re-sourced). Flipped back to `Sourced`, Gate 0 `Not checked`.
- **Stays `Sourced`, genuinely unconfirmed (5):** Coach Marios, Coach Bethany,
  Priya (Living liife), Andrew Nicholson (name collision + brand-name IG
  handle made the audience channel unlocatable after 3 searches), Dr. Marjan
  Dorkhan (above).
- **Data-hygiene fix:** Ayo Nova's `Audience Size` was reconciled from a stale
  12,929 (an old sourcing-time read) to the verifier-reproduced LinkedIn
  number, 2,754 — both clear the floor, only the stored number was off.
- **0 of 10 promotions overturned** — well under the ≥2 threshold, no batch
  redo needed.
- **Walk Queue now has 10 rows at `Qualifying`**, up from 0. Next step is
  `batch-audit`/`process-lead` to walk them.

## 2026-07-20 — Sourcing top-up: 17 new Sourced rows across 5 veins

Ran a top-up sourcing run (source-leads skill, chassis-compliant): pulled the
full 338-row CRM dedup snapshot, checked Apify quota (6.1% of cap, healthy),
fanned out 5 `sourcing-worker`s in parallel (platform footprint, link-in-bio,
LinkedIn, coach directories, podcasts/events), merged + cross-vein-deduped
their 18 raw candidates, ran a `sourcing-verifier` pass, then wrote the 17
cleared survivors as `Sourced` rows.

- **Produced:** coach directories 7 (Skilldeer/Mentaa priced booking pages —
  strong new vein, marketplace listing = the funnel), LinkedIn 4 (Ayo Nova,
  Jonny Parr, Wardah Harharah + Chenyang Zhao dropped by verifier — see
  below), platform footprint 4 (Tanner Shuck, Andrew Nicholson, Coach El,
  Caleb Jones — kajabi-footer/skool/kartra subdomains), link-in-bio 3 (Dan
  Chadwick, Nikoleta Perinova, Coach Bethany).
- **Dry:** podcasts/events came up with zero new candidates — heavily
  pre-mined (10 dedup hits), remaining surface skews agency/B2B/non-UAE. Flag
  for next run: point elsewhere.
- **Verifier dropped 1:** Chenyang Zhao (teamaspirecoaching.com) — reads as a
  small team ("your success coach", in-house psychotherapist, weekly team
  Zoom) not solo, plus no purchasable offer (application-only, staging-domain
  CTA). Two flagged candidates resolved to PASS on re-check: Dr. Marjan
  Dorkhan (price found, 985/1,095 AED) and Jonny Parr (UAE base confirmed —
  Sharjah, stated on-site).
- **Standout audience:** Ayo Nova, 12,929 (thebrilliantwoman.com, Scale
  Mastermind $599-799/mo via live Stripe checkout). Coach El logged with a
  genuine but tiny audience (~6 members) — likely a Gate 0 audience-floor
  fail downstream, noted in Notes rather than dropped at sourcing.
- **CRM now has 18 rows at `Sourced`** (17 new + 1 carryover). Next step is
  `qualify-leads` on this pile before any of it reaches the Walk Queue.

## 2026-07-20 — uae-tick: reconciled 30 rows to Gmail reality, Rita Baki said yes to Loom

Ran the daily uae-tick over both inboxes. The heavy lift was reconciling yesterday's scheduled batch against Gmail reality — nothing new was drafted today (no follow-ups due except one Loom action).

- **Reconciled 30 rows to match Gmail departures**, full confirmed-send checklist each (Touch #, Last Contacted, Next Action, Findings Bank flip, pre-send Notes markers cleared):
  - 15 fresh Touch-1 openers departed this morning (8 Inbox 1: Sadia Khan, Bonge Gumede, Monika Singh, Asma Ahmad, Aleli Carissa Gimena, Caroline Bakker, Nabil El Fquir, Dr. Jamila Al Hosani; 7 Inbox 2: Dr. Corrie Block, Trisha Hazarika, Samira Alexander, Nikki Evans, Sanjukta Ghosh, Sabeen Javed, Kalyani Seth Soni). Asma Ahmad's row had a blank `Inbox` property despite her draft living in Inbox 1 — set it during reconciliation.
  - 14 cold Touch-2 sends from the 07-19 batch departed on schedule (8 Inbox 1 + 6 Inbox 2, per yesterday's list) — bank #2 flipped USED-T2 on each (Jana Masri Vintrova excepted, single-finding row, loom-offer carrier, no bank spend).
  - Lisa Hugo's warm Touch-3 bump departed (Inbox 2) — logged, no bank spend.
- **Send-day 07-20 load, cap 20/inbox:** Inbox 1 = 16 (8 openers + 8 T2), Inbox 2 = 14 (7 openers + 6 T2 + Lisa). Both ≤ 20, headroom 4/6.
- **Rita Baki replied 07-20 07:28 Dubai, verbatim: "Yes please, a walkthrough would be great. Thank you for offering."** — said yes to the Loom offer from Touch 2. Logged to her Email Thread Log + Notes. This needs Haytham to record and send the Loom before price discovery can go out — flagged at the top of the brief, not something the tick can draft.
- **Bottleneck confirmed: hook+draft stage, not sends.** 10 Audit Ready leads (Daria Ibrulj, Szilvia Vitos, Wafa Bassili, Nadine Faddul, Joel Arcus, Eric Fit, Dr. Sheen Gurrib, Fatima Williams, Lee Harris, Zeina Karrit) are sitting on both hard gates with zero SMYKM Hook — none can draft until `haytham-hook-finder` runs. Today's 10 slots of send headroom go unused without it.
- **Gotcha:** Notion's `notion-query-data-sources` SQL tool hit its free-plan hourly quota partway through the tick (`entitlement_required` error) — pipeline-stage counts (Sourced/Qualifying totals) were unavailable for the rest of the run. Everything touching send state, replies, and hygiene was already queried before the cap hit, so the brief itself wasn't degraded, but a future tick that front-loads big SELECT * pulls should watch for this ceiling.
- **Gotcha:** Notion's `notion-update-page` `page_id` param requires a dashed UUID — passing the `https://app.notion.com/<32-hex>` URL straight (as `notion-fetch` accepts) 400s. Converting to `8-4-4-4-12` dashes fixed it; worth remembering next time a tick does bulk writes.
- No new bounces or hygiene breaks — clean sweep (no impossible Offer Sent states, no un-flipped bank entries, no leftover pre-send Notes markers, no future-dated Last Contacted). Pipeline is under a week old, so no scoreboard due yet.
### Open follow-ups
- [ ] Haytham: record + send the Loom walkthrough for Rita Baki, then ask price discovery.
- [ ] Run `haytham-hook-finder` on the 10 Audit Ready leads to unblock today's send headroom.
- [ ] Watch Neha Nimje's swapped address (contact@bizexconsultancy.com) for a second bounce.

## 2026-07-18 to 2026-07-19 — Pipeline build-out: agent verification chassis, Lane 2 status, first sends & replies

Condensed from ~530 lines of session-by-session detail — full verbatim
version (exact CRM values, per-lead agent transcripts, thread quotes) is in
`docs/journal-archive.md`. This is the two-day span that took the pipeline
from freshly-migrated to sending its first real batches.

**Dev — agent verification chassis (biggest structural change).** Root
cause of low agent-output quality: every stage let one context self-certify
the claim that ships. Fixed by giving each of the four stages the same
shape — least-privilege workers fan out and propose, an independent
verifier re-derives the one send-critical claim from scratch, the
orchestrator cross-checks Notion (`docs/agent-orchestration.md`). Landed
`finding-verifier`, `hook-verifier`, `qualifier-verifier`, `sourcing-verifier`
alongside their worker counterparts; smoke-tested finding-verifier and
hook-verifier on real leads (both correctly VERIFIED a true claim and
REFUTED a fabricated one). Same session: Qualifying overhaul to
resolve-then-decide (cheapest tool per datum — Firecrawl first, then a
no-login Apify actor for a login-walled LinkedIn/IG/YouTube count instead of
stalling at "Not checked"), a new blessed `youtube_channel` actor, and the
hook+draft stage merged into one draft-first pass (hook-worker →
hook-verifier → orchestrator drafts immediately, Haytham reviews finished
drafts instead of a bare-hook table) — all now the standing behavior
documented in CLAUDE.md and the skills themselves.

**CRM schema — new "Lane 2" status.** Added and migrated 12 no-leak leads
into it from Dormant/Disqualified, giving no-leak operators a proper home
instead of being buried in unrelated buckets.

**First sends and warm threads.** Donna Brown and Lucia Csobonyei both went
warm, through Loom offers and (Donna) the first price-discovery question
asked and answered in the track's history. Rita Baki also went warm off her
Touch-1 reply, the earliest of her long thread documented later in this
journal. Several leads got re-walked after their original finding died or
was disputed (Nikki Evans, Corrie Block, Samira Alexander, Roota Mittal →
correctly landed on Lane 2, no forced send) and reached Audit Ready/Draft
Ready on fresh verified findings — including a same-day 6-lead batch
(Sanjukta, Sabeen, Trisha, Nabil, Aleli, Caroline) that fed directly into
that day's hook+draft run. Danish Ali and Sahar Huneidi Palmer were
disqualified (non-UAE residency; unreachable email) after real digging
ruled out the softer read.

**Lessons banked (still load-bearing):**
- **Firecrawl mobile screenshots are unreliable for layout/overlap/clipping
  claims on some sites** (stitching artifacts produced two false positives)
  — verify any layout-style finding on Playwright/desktop or raw HTML before
  trusting it. Content/headline mismatches read from HTML are safe as-is.
- **Never cold-text a lead on WhatsApp from Haytham's personal number** —
  one unsolicited message got his number spam-flagged/blocked within 6
  hours. Same family of risk as the Instagram ban; treat an
  autoresponder-only lead as a bot moat, not a channel to chase manually.
- **Notion's free-tier SQL query quota (`notion-query-data-sources`) runs
  out mid-session regularly** — page-level fetch/update/create keeps
  working; fall back to `notion-query-database-view` on an unfiltered view
  (paginated) for a full-CRM read when SQL is capped.
- **`caprolok/website-email-phone-finder` + `vulnv/linkedin-email-finder`**
  (cost-gated Apify actors, not in the original blessed set) can find a
  genuinely published email that `email-enrich`'s name-guessing can't —
  useful when a lead's only address is dead and enrich would just re-derive
  the same dead guess. When the walk's email step gives up after checking
  only the funnel domain, sweeping the lead's other owned channels (YouTube
  About, Facebook page, a separate branded site) before declaring "not
  found" surfaced two otherwise-missed addresses the same week — worth
  remembering if the email step ever stalls again on a lead with an
  obviously active public presence.
- Instagram fetch was split into two dedicated sibling actors
  (`instagram-profile-scraper` / `instagram-post-scraper`, both PAY_PER_EVENT,
  same field names) for a cleaner, slightly cheaper equivalent of the old
  single scraper — CLI command names unchanged.
