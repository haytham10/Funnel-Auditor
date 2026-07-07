---
name: batch-audit
description: Work a whole sourcing session's worth of leads in one run, pulled from Notion instead of pasted into chat. Use WHENEVER Haytham says "batch audit," "work the queue," "I just finished sourcing," "fetch the new leads from Notion and work them," or names several leads already logged in the pipeline. It queries the Lead Pipeline for fresh Researching rows, then runs the full process-lead flow on each (machine walk → floors → opener-finder → Notion write → email address → draft), and finishes with one batch brief plus per-lead draft variants awaiting approval. Gmail DRAFTS only — it never sends and never touches Instagram.
---

# Batch Audit — sourcing session → worked pipeline

Haytham's sourcing habit: browse IG manually, log candidates straight into
Notion as he goes, then hand the whole batch over. This skill picks the batch
up from Notion — chat paste not required.

## What he logs at sourcing time (the intake contract)

Minimum per row: **Contact Name + Site URL** (the link-in-bio). Wanted:
Profile URL, Followers, Source. Anything else the system fills.

## Step 1 — Fetch the batch

Query `collection://c6209e29-55ef-4781-b735-73b2a254e34f` for rows with
Status = 'Researching' AND Site URL set, newest first. If Haytham named
specific leads or said "today's", filter accordingly.

Also query Researching rows with NO Site URL and list them at the end as
"need the bio link" — never try to get it from Instagram.

Cap a single run at ~8 leads (quality of the walk beats throughput; the
email gate loop is expensive). More than that: work the first 8 —
sub-12K-follower rows first, then newest — and name what's left for the
next run.

State the batch in one line ("Working 6: Jane, Maria, …") and start. Do not
wait for confirmation — he handed the batch over by logging it.

## Step 2 — Work each lead, start to finish

For each lead, run the **process-lead** skill's steps exactly (read
`.claude/skills/process-lead/SKILL.md` once at the start and follow it per
lead): machine walk via `python main.py walk`, complete the floors (web
search for activity + SMYKM material), opener-finder walk + lane call,
Notion page body + properties in the exact schema, Email OS address tree.

Batch-specific rules:
- The row already exists — update it, don't create a duplicate.
- A floor fail or Lane 3 is a fine outcome: park it properly (Tier 4,
  Disqualified, one-line reason) and move on without ceremony.
- If one lead's crawl breaks, note it and continue the batch — never let one
  bad site stall the session.
- Draft the Touch 1 email (haytham-email-draft skill, full silent gate loop)
  for every Lane 1/2 lead with an address, but HOLD all drafts for the end.

## Step 3 — The batch brief (one message)

1. **Table**: lead / lane / tier / strongest finding in one line / email
   address status / draft ready?
2. **Drafts**: per Lane 1/2 lead, the labeled variants (subject + body),
   grouped by lead, each with its innocent explanation + SMYKM hook noted.
3. **Parked**: Lane 3 leads with their one-line reasons.
4. **Blocked**: rows needing a bio link or an email address, with the
   specific manual step (freebie opt-in, pattern-guess + verify).

Then stop and wait. Approvals come back like "approve Jane A, Maria B, skip
Leah" → create one Gmail draft per approved variant. Logging (Email Thread
Log + full property diff, per the email-draft skill) happens only when he
confirms a send with "log Jane" / "log this" — never at draft or Gmail-draft
time, because Status = Outreach Sent must mean the email actually left.

## Hard rules

- Never send an email. Gmail drafts only, and only after approval.
- Never fetch or automate anything on instagram.com. Rows without a Site URL
  wait for him.
- Never invent findings to make a batch look productive — a batch of six
  with two real openers beats six manufactured ones.
- Notion is the source of truth; re-read the row before writing it.
