---
name: batch-audit
description: Work a whole sourcing session's worth of leads in one run, pulled from Notion instead of pasted into chat, in parallel with one lead-processor agent per lead. Use WHENEVER Haytham says "batch audit," "work the queue," "I just finished sourcing," "fetch the new leads from Notion and work them," or names several leads already logged in the pipeline — and when the scheduled lead-queue Routine fires. It queries the Lead Pipeline for fresh Researching rows, runs the full process-lead flow on each (machine walk → vision pass → floors → opener-finder → Notion write → email address → Gmail DRAFT), and finishes with one batch brief. Gmail DRAFTS only — it never sends and never touches Instagram.
---

# Batch Audit — sourcing session → worked pipeline, in parallel

Haytham's sourcing habit: browse IG manually, log candidates straight into
Notion as he goes — Contact Name + Site URL in the properties, and his IG
screenshots (profile, recent posts, link-in-bio) dropped into the page body.
Then the system takes over. This skill picks the batch up from Notion — chat
paste not required.

## What he logs at sourcing time (the intake contract)

Minimum per row: **Contact Name + Site URL** (the link-in-bio). Wanted:
Profile URL, Followers, Source, and **IG screenshots attached to the page
body** — they're the only Instagram signal the system is allowed to have.
Anything else the system fills.

## Step 1 — Fetch the batch

Query `collection://c6209e29-55ef-4781-b735-73b2a254e34f` (MCP data source) for rows with
Status = 'Researching' AND Site URL set, newest first. (REST API database ID: `78b26ebe-5b4f-4ff2-884a-3ccf369d00e6`.) If Haytham named
specific leads or said "today's", filter accordingly. Skip rows whose Notes
first line says an email/address problem is waiting on HIS manual step —
re-running the walk won't fix those.

Also query Researching rows with NO Site URL and list them at the end as
"need the bio link" — never try to get it from Instagram.

Cap a single run at **15 leads**. More than that: work the first 15 —
sub-12K-follower rows first, then newest — and name what's left for the
next run.

State the batch in one line ("Working 6: Jane, Maria, …") and start. Do not
wait for confirmation — he handed the batch over by logging it. If the run
came from the scheduled Routine and the queue is empty, say "Queue empty —
nothing sourced since last run" and stop.

## Step 2 — One lead-processor agent per lead, ~3 at a time

Run `pip install -q -r requirements.txt` once before spawning anything.

For each lead, spawn a **lead-processor** agent (`.claude/agents/
lead-processor.md`). Its prompt must contain everything it needs — agents
start cold: the lead's Notion page URL/ID, Contact Name, Site URL, Profile
URL, Followers, Source, plus any batch-specific note Haytham gave. Tell it
the row already exists — update, don't duplicate.

Concurrency: keep **at most 3 agents running**; as one completes, launch the
next. Each agent works one lead start-to-finish per the process-lead skill —
machine walk, vision pass, floors, opener-finder walk + Notion write, email
address, and the automatic Gmail DRAFT — and returns the structured LEAD
block defined in the agent file.

Batch rules the orchestrator enforces:
- A floor fail or Lane 3 is a fine outcome: parked properly (Tier 4,
  Disqualified, one-line reason) counts as done.
- If one agent errors or its crawl breaks, record it under Blocked and keep
  the batch moving — never let one bad site stall the session.
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
confirm the Gmail drafts exist (`list_drafts` once, match subjects). An
agent that claimed success but wrote nothing goes under Blocked, not Done.

Then one brief, in this order:

1. **Table**: lead / lane / tier / strongest finding in one line / email
   status / Gmail draft? / IG evidence seen? / flags rejected.
2. **Drafted**: per lead with a Gmail draft — the drafted subject + body in
   full, plus labeled runner-up variants, each with its innocent explanation
   noted. SMYKM hook will read "not run yet" for every lead in this batch —
   that's expected, since `haytham-hook-finder` is a separate, manual step;
   name it as available if Haytham wants a stronger opener on any of these
   before sending. He edits or swaps in Gmail and sends by hand.
3. **Held**: Lane 1/2 leads where the draft was held (suspect address,
   gate never passed) with the specific reason.
4. **Parked**: Lane 3 leads with their one-line reasons.
5. **Blocked**: rows needing a bio link, an email address, or a re-run after
   a crawl failure, each with the specific manual step.
6. **Leftover queue**: anything past the 15-cap, named for the next run.

Sending is Haytham's hand, from Gmail. Logging (Email Thread Log + full
property diff, per the email-draft skill) happens only when he confirms a
send with "log Jane" / "log this" — never at Gmail-draft time, because
Status = Outreach Sent must mean the email actually left.

## Hard rules

- Never send an email. Gmail drafts only.
- Never fetch or automate anything on instagram.com. IG evidence comes only
  from the screenshots attached to the Notion page. Rows without a Site URL
  wait for him.
- Never invent findings to make a batch look productive — a batch of six
  with two real openers beats six manufactured ones. Machine flags the
  vision pass rejected stay rejected.
- Notion is the source of truth; agents re-read the row before writing it.
- Creating a Gmail draft never advances Status/Touch #/Last Contacted.
