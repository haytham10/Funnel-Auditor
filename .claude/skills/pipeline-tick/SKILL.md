---
name: pipeline-tick
description: The daily outreach ops loop over the Notion Lead Pipeline and Gmail. Use WHENEVER Haytham says "tick," "morning brief," "what's due," "check the pipeline," "any replies," or when a scheduled Routine fires this skill. It detects replies in Gmail and syncs pipeline state, surfaces and drafts the follow-up touches that are due, flags dormant leads ready for a revival bump, and hands over today's send queue. It creates Gmail DRAFTS only — it never sends, and it never advances Touch #/status for an email that hasn't actually been sent.
---

# Pipeline Tick — replies, due touches, send queue (PARENTING TRACK ONLY)

**Scope (Jul 13, 2026): this skill covers the parenting track only, and
that track is live-threads-only — no new leads get sourced into it.** The
active pipeline is the UAE track, which has its own daily loop
(`uae-tick`) over its own CRM. If Haytham says "tick" without naming a
track, the UAE tick is the default; run this one when he says "parenting
tick," when a parenting-thread reply needs handling, or on its own
schedule. Section 3's send queue below will naturally be empty or near
empty — that's correct, not broken. Never write a UAE lead into this DB.

Run the whole loop, then deliver one morning brief. Notion is the source of
truth — never trust chat memory for pipeline state.

Pipeline data source (MCP): `collection://c6209e29-55ef-4781-b735-73b2a254e34f`.
Database ID (REST API): `78b26ebe-5b4f-4ff2-884a-3ccf369d00e6`.

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

**The leash (2026-07-14 — this track shares the UAE track's one domain,
and its bump batches were the biggest spam signal in the sent log):**

- **Max 5 parenting sends per day**, inside the shared ceiling — never in
  addition to it. Warm threads and scheduled dormant revivals only.
- **No bare cold bumps, ever.** A cold-thread follow-up that adds nothing
  new is dead on this track — the 19-bumps-in-two-minutes batches to
  never-replied threads are over. A cold touch goes out only if it
  carries something real (the same carry standard as the UAE gate: a new
  observation, the Loom offer, or a closing disambiguating question);
  otherwise the thread goes Dormant with a revival date and waits.
- **Never more than 10 sends in one sitting, and never a same-minute
  batch** — spread them. Burst-sending from one inbox is a pattern
  filters key on, independent of volume.

For each due row that survives the leash, identify the touch type from
Sequence + Touch # + Status (warm bump, dormant back-from-the-dead, cold
Touch 2/3/4 WITH a real carrier) and draft it with the
**haytham-email-draft** skill — full loop, correct email type, mechanics
cadence.

Then create the Gmail DRAFT automatically for the strongest variant — with
one guard: check Gmail drafts first (`list_drafts`), and if an unsent draft
to that address already exists, do NOT stack a second one; surface the old
draft in the brief instead ("draft from <date> still unsent — send, edit,
or delete"). Warm replies (turn-two moves) are drafted as replies in the
existing thread (`replyToMessageId`). Deliver every draft in the brief as
labeled variants per lead, marking which variant is sitting in Gmail.

Do NOT log or increment anything at draft time — a Gmail draft is not a
send. Only after Haytham confirms a send does the logging + property diff
happen (per the email-draft skill's rules, including Touch 4 → Dormant with
a 2-3 week revival date, never Lost for a cold no-reply).

## 3 — Send queue

Query Status = Audit Ready with an Email set. Sort sub-12K followers first
(the warm-reply band so far), then Tier. Present as "ready to send today" —
Email OS daily input is 3 cold sends + 1 follow-up.

Every send from this track leaves **Inbox 1** (haytham@auto-mate.one, the
primary — this track never uses Inbox 2) and counts against Inbox 1's own
daily ceiling (`python main.py send-cap status` with no --inbox reads
exactly that inbox; fails closed to 20). uae-tick's Inbox 1 sent-count
picks these up automatically; if today's UAE Inbox 1 queue is already at
that ceiling, parenting sends displace it one-for-one — say so in the
brief rather than silently stacking past it. Inbox 2's headroom is UAE
capacity, never a parenting overflow valve. The 5/day parenting leash applies on top: the UAE
track is the active pipeline, and this track's live threads never
out-consume it.

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
  Contacted, or Next Action for an unsent email — creating a Gmail draft is
  not a send.
- Reply-detection updates (Status/Sequence on a real reply, verbatim reply
  logging) are the ONLY Notion writes this skill makes without approval —
  they record reality, they don't create outreach.
- Never stack a second unsent draft to the same address.
- Never log in to or act as Haytham on any platform (Instagram included).
