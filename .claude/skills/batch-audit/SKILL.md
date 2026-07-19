---
name: batch-audit
description: Work a whole batch of UAE leads in one run, pulled from the UAE Lead CRM's Walk Queue instead of pasted into chat, in parallel with one lead-processor agent per lead. Use WHENEVER Haytham says "batch audit," "work the queue," "work the walk queue," "run the walks," or names several leads already logged in the CRM — and when a scheduled Routine fires it. It queries the UAE Lead CRM for Qualifying rows ready for a walk, runs the process-lead flow on each (machine walk → vision pass → Gate 0 floors → opener-finder → Notion write → email address), and finishes with one batch brief. Gmail drafts are held: no lead gets a draft in this run — the walk ends held at Audit Ready, and drafting happens later in the merged hook+draft stage (`haytham-hook-finder`, draft-first). It never sends, and never logs in to or automates anything through Haytham's own platform accounts.
---

# Batch Audit — walk queue → worked pipeline, in parallel

Sourcing is dynamic and no-login now: the `source-leads` skill (or Haytham
by hand) logs candidates into the UAE Lead CRM as `Sourced`, then
`qualify-leads` gates them to `Qualifying`. Then the system takes over. This skill picks the
batch up from Notion — chat paste not required.

**CRM:** `collection://5efbdd9b-1e19-468c-96db-f94a525846e0`
(REST API database ID: `5a9fc583160046d1a64c4e65cc804229`).
Walk Queue view: `39c382c8-4585-8194-bba1-000cf32dee66`.
**NEVER write to the old parenting DB** (`c6209e29-55ef-4781-b735-73b2a254e34f`).

## What a row needs before this skill can work it (the intake contract)

Minimum per row: **Contact Name + Site URL** (the funnel entry point).
Wanted: Profile URL (LinkedIn), Audience Size, City, Source Channel.
Anything else the system fills.

## Step 1 — Fetch the batch

Query the 🔬 Walk Queue view (`39c382c8-4585-8194-bba1-000cf32dee66`), or
equivalently by SQL: Status = 'Qualifying' AND Site URL set, gates-passed
rows first (`Gate 0` = 'Pass' AND `Gate 1` = 'Pass'), then rows whose
gates are still 'Not checked' (the lead-processor enforces Gate 0 floors
itself either way), newest first. If Haytham named specific leads or said
"today's", filter accordingly. Skip rows whose Notes first line says an
email/address problem is waiting on HIS manual step (e.g. "email not found —
enrichment attempted, no verified candidate; freebie opt-in needed") —
the walk already ran nominative enrichment, so re-running it won't fix those.

Also list rows with NO Site URL at the end as "need the site link" —
never try to fill it from anything but a public web search.

**The run cap = 20 leads** ("the run cap" everywhere below) — a full day of
sends at one inbox's first ceiling step. But size the actual batch to
**downstream send headroom**, not blindly to 20: check `python main.py inbox
counts` + `python main.py send-cap status --all`; if the next send-day's opener
headroom across both inboxes is only ~8, walking 20 just ages findings with
nowhere to go — walk to the headroom, capped at the run cap. More than that in
the queue: work up to the run cap and name what's left. A walk with nowhere to
send is a wasted walk (`docs/agent-orchestration.md`, demand-driven sizing).

State the batch in one line ("Working 6: Jane, Maria, …") and start. Do
not wait for confirmation — he handed the batch over by logging it. If
the run came from a scheduled Routine and the queue is empty, say "Walk
queue empty — nothing qualified since last run" and stop.

## Step 2 — One lead-processor agent per lead, ~5 at a time

Run `pip install -q -r requirements.txt` once before spawning anything.

**Check the Apify quota once, before spawning anything (added Jul 15,
2026, after a batch where several agents each separately burned tool
calls discovering the same exhausted monthly quota):** `python main.py
apify limits`. Apify's plan caps on a monthly USD budget
(`current.monthlyUsageUsd` vs `limits.maxMonthlyUsageUsd`), not a
per-actor credit — one lead's LinkedIn/IG lookups can burn a meaningful
slice of it. If `near_cap` is `true` (or a call errors), tell every
lead-processor agent in its prompt: "Apify is at/near its monthly cap
this run — do not call `python main.py apify <anything>` for audience
confirmation; note 'Apify unavailable this run' and proceed on
Firecrawl/web-search signal alone." One check, not one per lead.

Separately, every individual Apify call is also cost-gated per-run
(`audit/apify.py`, $0.10 threshold) — a normal single-lead pull clears it
automatically, but if a lead-processor agent reports `APPROVAL REQUIRED`
(exit 3, `EMAIL VERIFY`/`EMAIL ENRICH: APPROVAL REQUIRED`, or an
`apify <cmd>` call printing `needs_approval`), do not tell it to retry —
surface the estimate to Haytham and only re-run with `--approve-cost`
once he's said yes.

For each lead, spawn a **lead-processor** agent (`.claude/agents/
lead-processor.md`). Its prompt must contain everything it needs — agents
start cold. **Prompt-assembly checklist (a missing field silently degrades that
walk):** the lead's Notion page URL/ID, Contact Name, Site URL, Profile URL,
Audience Size, City, Source Channel, the Apify-quota note above, any
batch-specific note Haytham gave, "the row already exists — update, don't
duplicate," and the reminder that it **proposes** the finding and must NOT check
`Finding Verified` (the finding-verifier does that in Step 2.5).

Concurrency: keep **at most 5 agents running at once, of any kind** —
lead-processors and the Step 2.5 finding-verifiers share that budget. As one
completes, launch the next; verifiers are short and drain fast. Each
lead-processor works one lead start-to-finish per the process-lead skill —
machine walk, vision pass, floors, opener-finder walk + Notion write, email
address — and holds at Audit Ready, no Gmail draft (every lead comes back with the
hook line "not run yet"; the walk never drafts — the merged hook+draft stage
`haytham-hook-finder` does that later). It returns the structured JSON block
defined in the agent file, with the finding **proposed** (`finding_verified:
"proposed"`) and the exact evidence paths it rests on.

Batch rules the orchestrator enforces:
- A floor fail or Lane 3 is a fine outcome: parked properly (Gate fail,
  Disqualified, one-line reason) counts as done. So does Lane 2 (set to
  Status `Lane 2`, the dedicated no-leak status — no verified finding means
  no cold send, by design).
- If one agent errors or its crawl breaks, record it under Blocked and
  keep the batch moving — never let one bad site stall the session.
- Never spawn two agents for the same lead, and never re-run a lead that
  already returned its block.

**Stall guardrail (added Jul 10, 2026, after a prior run burned 84.5K+
tokens on a stuck agent):** if a lead-processor agent returns a status-only
reply — a stub like "waiting on the walk to finish" or "waiting for the
monitor's notification," with no new tool calls or work product since its
last turn — that is one stall. Do not resume that agent a second time and
do not send another nudge. Take the lead over directly: check
`evidence/<slug>/` for whatever the agent already produced (walk output,
vision manifest, packet), confirm with `ps aux` / background-process status
whether anything is genuinely still running, and finish the lead yourself
from that point with direct tool calls per `.claude/skills/process-lead/
SKILL.md`. The only exception is concrete evidence of active progress (a
real running process with recent file writes) — let that finish, but
monitor it yourself rather than re-dispatching the agent. Record the
takeover in the batch brief the same as any other lead; it still counts as
worked, not Blocked, if you finished it.

## Step 2.5 — Verify each Lane 1 finding (independent)

A lead-processor PROPOSES its finding and never checks `Finding Verified` — that
self-certification is exactly what shipped false Lane-1 findings, so an
independent pass certifies (`docs/agent-orchestration.md`). For every return with
**Lane 1** and a proposed finding, spawn a **`finding-verifier`**
(`.claude/agents/finding-verifier.md`); it shares the ≤5 concurrency budget with
the still-running walkers. **Verifier prompt-assembly checklist:** the finding
text, the innocent explanation, the lane, the lead's Notion page URL/ID, the
`evidence/<slug>` dir, and the **exact cited paths** from the worker's
`finding_evidence_paths`, with the framing "assume it's false until a cited
screenshot forces you to agree." Lane 2 / Lane 3 / gate-fail returns skip the
verifier — they never send.

Act on each verdict:
- **VERIFIED** → the verifier already checked `Finding Verified` and promoted
  (Audit Ready if `Email Verified` is set, else held at Qualifying). Ready for §2.
- **REFUTED** → the finding is dead. If the walk still found real structure
  (plausibly Lane 1, wrong finding), re-dispatch **one** lead-processor with the
  refutation as guidance (cap at one re-walk); otherwise set it to Lane 2.
- **INCONCLUSIVE** → holds at Qualifying with the reason.

**Quality tripwire:** if the verifier REFUTES **≥2 of the first wave's Lane 1
findings**, pause the batch and surface it to Haytham before spending the rest of
the queue — a high refute rate is the machine catching its own bad night.

## Step 3 — Cross-check, then the batch brief (one message)

Cross-check before reporting — the return block is a report, never the source of
truth. For each Lane 1/2 result, `notion-fetch` the row and confirm the body
carries the fresh walk AND matches the return block (the finding text, the
`Findings Bank` count, the literal `VISION PASS:` line). For each Lane 1,
`Finding Verified` should now be checked **by the finding-verifier** (VERIFIED
leads) or explicitly not (REFUTED/INCONCLUSIVE) — a box the walker checked itself,
or a claim of success over a row that wasn't written, goes under Blocked, not
Done. No Gmail drafts are expected from this run — don't check `list_drafts`.

Then one brief, in this order:

1. **Table**: lead / gates / lane / strongest finding in one line /
   Finding Verified? / email status (incl. the `EMAIL VERIFY` verdict for
   Lane 1) / vision-pass line / flags rejected.
2. **Ready for the hook+draft stage**: every Lane 1 lead that is actually
   Audit Ready — `Finding Verified` AND `Email Verified` both checked (an
   independently VERIFIED finding — the finding-verifier's verdict, not the
   walker's — plus a deliverability-confirmed address) — the walk finding +
   innocent explanation in full, one line each. These are the queue for the
   merged **hook+draft stage** (`haytham-hook-finder`, draft-first): when
   Haytham runs it, it resolves the hook and creates the held Gmail draft in
   one pass. A Lane 1 lead whose address came back `EMAIL VERIFY: WARN/FAIL`
   is NOT here — it's in §4 (held), holding at Qualifying.
3. **Warm-up holds (Lane 2)**: committed buyers with no felt leak — the
   warm-up angle, one line each. These are set to Status `Lane 2` (the
   dedicated no-leak status) and never enter the cold send queue; Haytham
   works them by hand if and when he wants.
4. **Held for other reasons**: Lane 1 leads with a verified finding still
   short of Audit Ready — an address that came back `EMAIL VERIFY:
   WARN/FAIL` (holding at Qualifying, needs a better address or Haytham's
   risk call), a suspect-source address, or no address — with the specific
   reason.
5. **Parked**: gate fails and Lane 3 leads with their one-line reasons.
6. **Blocked**: rows needing a site link, an email address, or a re-run
   after a crawl failure, each with the specific manual step.
7. **Leftover queue**: anything past the run cap (20), named for the next run.

Sending is Haytham's hand, from Gmail, and every cold send passes
`python main.py crm-gate send` at queue time (uae-tick owns that).
Logging (Email Thread Log + full property diff, per the email-draft skill)
happens only when he confirms a send with "log Jane" / "log this" — never
at Gmail-draft time, because Status = Outreach Sent must mean the email
actually left.

## Hard rules

- Never send an email. Gmail drafts only.
- Never log in to or act as Haytham on any platform (Instagram and
  LinkedIn included) — the account-safety rule the IG ban was about, not a
  blanket ban on Instagram as data. Read-only public data through a
  no-login third-party tool is fine on any platform. Rows without a Site
  URL wait for him.
- Never invent findings to make a batch look productive — a batch of six
  with two real openers beats six manufactured ones. Machine flags the
  vision pass rejected stay rejected, and `Finding Verified` never gets
  checked to make a lead sendable.
- Notion is the source of truth; agents re-read the row before writing it.
- Creating a Gmail draft never advances Status/Touch #/Last Contacted.
- No agent creates a Gmail draft in this run. The hook line always reads
  "not run yet" straight out of opener-finder; the walk holds at Audit Ready,
  and drafting belongs to the merged hook+draft stage (`haytham-hook-finder`,
  draft-first), which Haytham runs separately.
- Never write a UAE lead into the parenting DB.
