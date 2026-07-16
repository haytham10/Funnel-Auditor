---
name: batch-audit
description: Work a whole batch of UAE leads in one run, pulled from the UAE Lead CRM's Walk Queue instead of pasted into chat, in parallel with one lead-processor agent per lead. Use WHENEVER Haytham says "batch audit," "work the queue," "work the walk queue," "run the walks," or names several leads already logged in the CRM — and when a scheduled Routine fires it. It queries the UAE Lead CRM for Qualifying rows ready for a walk, runs the process-lead flow on each (machine walk → vision pass → Gate 0 floors → opener-finder → Notion write → email address), and finishes with one batch brief. Gmail drafts are held: no lead gets a draft in this run — that only happens after Haytham runs `haytham-hook-finder` on a lead and asks for the draft. It never sends, and never logs in to or automates anything through Haytham's own platform accounts.
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
email/address problem is waiting on HIS manual step — re-running the walk
won't fix those.

Also list rows with NO Site URL at the end as "need the site link" —
never try to fill it from anything but a public web search.

Cap a single run at **20 leads** — a full day of sends at the ramp's
first ceiling step, so a bigger batch of walks has nowhere to go anyway.
More than 20 in the queue: work the first 20 and name what's left for
the next run.

State the batch in one line ("Working 6: Jane, Maria, …") and start. Do
not wait for confirmation — he handed the batch over by logging it. If
the run came from a scheduled Routine and the queue is empty, say "Walk
queue empty — nothing qualified since last run" and stop.

## Step 2 — One lead-processor agent per lead, ~5 at a time

Run `pip install -q -r requirements.txt` once before spawning anything.

**Check the Apify quota once, before spawning anything (added Jul 15,
2026, after a batch where several agents each separately burned tool
calls discovering the same exhausted monthly quota):** `python main.py
apify limits`. Apify's free/starter tier caps on a small monthly USD
budget (`current.monthlyUsageUsd` vs `limits.maxMonthlyUsageUsd`), not a
per-actor credit — one lead's LinkedIn/IG lookups can burn a meaningful
slice of it. If `near_cap` is `true` (or a call errors), tell every
lead-processor agent in its prompt: "Apify is at/near its monthly cap
this run — do not call `python main.py apify <anything>` for audience
confirmation; note 'Apify unavailable this run' and proceed on
Firecrawl/web-search signal alone." One check, not one per lead.

For each lead, spawn a **lead-processor** agent (`.claude/agents/
lead-processor.md`). Its prompt must contain everything it needs — agents
start cold: the lead's Notion page URL/ID, Contact Name, Site URL, Profile
URL, Audience Size, City, Source Channel, the Apify-quota note above, plus
any batch-specific note Haytham gave. Tell it the row already exists —
update, don't duplicate.

Concurrency: keep **at most 5 agents running**; as one completes, launch
the next. Each agent works one lead start-to-finish per the process-lead
skill — machine walk, vision pass, floors, opener-finder walk + Notion
write, email address — and holds at the Gmail draft (every lead comes back
with the hook line "not run yet," and drafting is blocked until
`haytham-hook-finder` runs on that lead). It returns the structured LEAD
block defined in the agent file.

Batch rules the orchestrator enforces:
- A floor fail or Lane 3 is a fine outcome: parked properly (Gate fail,
  Disqualified, one-line reason) counts as done. So does Lane 2 (holds at
  Qualifying as a warm-up lead — no verified finding means no cold send,
  by design).
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

## Step 3 — Verify, then the batch brief (one message)

Spot-check before reporting: for each Lane 1/2 result, confirm the Notion
page body actually carries the fresh walk (one `notion-fetch`, cheap), and
for each Lane 1, that `Finding Verified` is actually checked in the
properties. No Gmail drafts are expected from this run — don't check
`list_drafts` for them. An agent that claimed success but wrote nothing
goes under Blocked, not Done.

Then one brief, in this order:

1. **Table**: lead / gates / lane / strongest finding in one line /
   Finding Verified? / email status (incl. the `EMAIL VERIFY` verdict for
   Lane 1) / vision-pass line / flags rejected.
2. **Needs hook-finder**: every Lane 1 lead that is actually Audit Ready —
   `Finding Verified` AND `Email Verified` both checked (verified finding +
   a deliverability-confirmed address) — the walk finding + innocent
   explanation in full, one line each, ready to draft the moment Haytham
   runs `haytham-hook-finder` on it and asks for the draft. A Lane 1 lead
   whose address came back `EMAIL VERIFY: WARN/FAIL` is NOT here — it's in
   §4 (held), holding at Qualifying.
3. **Warm-up holds (Lane 2)**: committed buyers with no felt leak — the
   warm-up angle, one line each. These stay at Qualifying and never enter
   the cold send queue; Haytham works them by hand if and when he wants.
4. **Held for other reasons**: Lane 1 leads with a verified finding still
   short of Audit Ready — an address that came back `EMAIL VERIFY:
   WARN/FAIL` (holding at Qualifying, needs a better address or Haytham's
   risk call), a suspect-source address, or no address — with the specific
   reason.
5. **Parked**: gate fails and Lane 3 leads with their one-line reasons.
6. **Blocked**: rows needing a site link, an email address, or a re-run
   after a crawl failure, each with the specific manual step.
7. **Leftover queue**: anything past the 15-cap, named for the next run.

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
  "not run yet" straight out of opener-finder, and drafting is blocked
  until Haytham runs `haytham-hook-finder` on a lead.
- Never write a UAE lead into the parenting DB.
