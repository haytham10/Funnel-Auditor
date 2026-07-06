---
name: pipeline-tick
description: The daily outreach ops loop over the Notion Lead Pipeline and Gmail. Use WHENEVER Haytham says "tick," "morning brief," "what's due," "check the pipeline," "any replies," or when a scheduled Routine fires this skill. It detects replies in Gmail and syncs pipeline state, surfaces and drafts the follow-up touches that are due, flags dormant leads ready for a revival bump, and hands over today's send queue. It creates Gmail DRAFTS only — it never sends, and it never advances Touch #/status for an email that hasn't actually been sent.
---

# Pipeline Tick — replies, due touches, send queue

Run the whole loop, then deliver one morning brief. Notion is the source of
truth — never trust chat memory for pipeline state.

Pipeline data source: `collection://c6209e29-55ef-4781-b735-73b2a254e34f`.

## 1 — Reply detection (Gmail → Notion)

Query the pipeline for rows with Touch # ≥ 1 and Status in
(Outreach Sent, Reply Received, Loom Sent, Call Booked, Dormant).
For each row with an Email, search Gmail for threads with that address since
Last Contacted.

- New reply found and Notion doesn't reflect it → update: Status = Reply
  Received (or the later stage if a Loom/call already happened), Sequence =
  Warm, and quote the reply verbatim in the brief. Append the reply verbatim
  to the lead page's Email Thread Log entry it answers (`Reply:` line).
- A reply is the highest-priority item in the brief — warm threads are where
  80% of meetings come from.
- Also check for bounces (mailer-daemon in the thread): flag as bad address,
  set Notes first line, Status back to Researching.

## 2 — Due follow-ups

Query rows where Next Action ≤ today and Status not in (Won, Lost,
Disqualified).

For each due row, identify the touch type from Sequence + Touch # + Status
(cold Touch 2/3/4, warm bump, dormant back-from-the-dead) and draft it with
the **haytham-email-draft** skill — full loop, correct email type, mechanics
cadence. Deliver all drafts in the brief as labeled variants per lead.

Do NOT log or increment anything at draft time. Only after Haytham approves
does a Gmail draft get created; only after he confirms a send does the
logging + property diff happen (per the email-draft skill's rules, including
Touch 4 → Dormant with a 2-3 week revival date, never Lost for a cold
no-reply).

## 3 — Send queue

Query Status = Audit Ready with an Email set. Sort sub-12K followers first
(the warm-reply band so far), then Tier. Present as "ready to send today" —
Email OS daily input is 3 cold sends + 1 follow-up.

Flag any Audit Ready row with no Email as "needs address" with its Notes line.

## 4 — Hygiene flags (report, don't auto-fix)

- Incoherent rows: Lane 3 without Tier 4/Disqualified, Lane 1/2 carrying
  Tier 4, Status Outreach Sent with Touch # = 0.
- Stale threads: Sequence = Warm, no touch in > 4 days.
- Researching rows older than a week with no walk in the page body.

## The brief

One message, in this order: replies (verbatim, with suggested turn-two move —
the Loom offer), due follow-ups (with drafts), today's send queue, hygiene
flags. If a section is empty, one line saying so. If everything is empty:
"Pipeline quiet — nothing due today," and stop. Keep it scannable; he reads
this before coffee.

## Hard rules

- Drafts only. Never send. Never auto-advance Touch #, Status, Last
  Contacted, or Next Action for an unsent email.
- Reply-detection updates (Status/Sequence on a real reply, verbatim reply
  logging) are the ONLY writes this skill makes without approval — they
  record reality, they don't create outreach.
- Never query or touch Instagram.
