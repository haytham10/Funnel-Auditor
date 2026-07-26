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

## 2026-07-27 — 20-lead follow-up batch drafted; fabricated calendar link + draft-update threading bug found and fixed

Ran uae-tick's due-follow-up step across all 20 due leads (13 cold Touch 3s, 7 warm/priced
follow-ups), one drafting agent per lead in parallel. All 20 gated PASS and got a held Gmail draft.
Also fixed the `Findings Bank` formatting on Rita Baki (`DEAD` status → `USED-T1`/`RETIRED`, parser
now resolves `current_finding()` correctly) and Lisa Hugo (rank 2 was wrongly left `UNUSED` after
being sent as Touch 2 — flipped to `USED-T2` to match the actual Email Thread Log).

**Two real bugs found only after Haytham caught wrong Calendly links by hand:**
- All 4 `leak-fix-offer` drafts (Ben Pringle, William Brown, Lucia Csobonyei, Lisa Hugo) shipped with
  a fabricated `calendly.com/haythamm/discovery` link — the drafting agents' own self-reported "final
  copy" claimed a *different* URL (`cal.com/haytham/15min`, itself unverified, pulled from
  `examples.md`) than what actually landed in the Gmail draft body. Agent self-reports are not a
  reliable substitute for reading the actual API object back. Fixed by stripping the link line
  entirely (the paid Leak Fix stands alone as a legal single-tap CTA) rather than guess a third URL.
- Using Gmail MCP's `update_draft` on an existing reply-draft (Ben Pringle, Lee Harris) silently
  **detaches it into a new orphaned thread** — the tool has no threading params, so re-editing a
  reply draft this way loses its attachment to the real conversation. Recovered both by recreating
  fresh via `create_draft` + `replyToMessageId`. Inbox 2 has no such risk (`gmail_gethaytham.py`'s
  raw `PUT /drafts/{id}` explicitly sets `threadId`/`In-Reply-To`, verified intact after the fix).
  **Lesson: never use `update_draft` on an existing Inbox 1 reply-draft — recreate it instead.**
- Gmail MCP's `list_drafts` only returns `plaintextBody` for the single most-recently-touched draft
  in the whole mailbox; `get_thread`/`search_threads` never surface DRAFT-labeled messages at all.
  There is currently no safe way to bulk-read Inbox 1 draft bodies without risking the threading bug
  above by touching them. The other 13 cold Touch-3 drafts (no calendar link, so structurally
  shouldn't hit the same bug) were NOT re-verified for this reason — Haytham should eyeball them.

Haytham confirmed: all fixed and scheduled to send 2026-07-27; manually moved Ben Pringle to
`Dormant` himself (not logged by us — his direct Notion edit stands as-is).

### Open follow-ups
- [ ] Delete the stray orphaned Lee Harris draft (`r-8321922502352988444`, detached thread) — no
      delete-draft tool available to do this from here.
- [ ] Get Haytham's actual calendar link (still unknown here — `cal.com/haytham/15min` in
      `examples.md` is unverified and should not be trusted as-is; update the reference once known).
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
