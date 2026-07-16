---
name: uae-tick
description: The daily outreach ops loop over the UAE Lead CRM and Gmail. Use WHENEVER Haytham says "uae tick," "tick," "morning brief," "what's due," "check the pipeline," "any replies," or when a scheduled Routine fires this skill — for the UAE track (the parenting track's live threads have their own loop, pipeline-tick). It detects replies in Gmail and syncs CRM state (including logging price discovery answers verbatim the moment they land), surfaces leads due the discovery question, runs the crm-gate checks on everything about to move, drafts the follow-up touches that are due, hands over today's send queue capped at the deliverability ceiling, and keeps the weekly scoreboard honest. It creates Gmail DRAFTS only — it never sends, and it never advances Touch #/Status for an email that hasn't actually been sent.
---

# UAE Tick — replies, discovery, due touches, send queue

Run the whole loop, then deliver one morning brief. Notion is the source of
truth — never trust chat memory for pipeline state.

**CRM:** `collection://5efbdd9b-1e19-468c-96db-f94a525846e0`
(REST API database ID: `5a9fc583160046d1a64c4e65cc804229`).
Views: 🔥 Today `39c382c8-4585-816e-bad3-000c4011b5df`, 📤 Send Queue
`39c382c8-4585-81aa-9d49-000c0ad49a3f`, 💬 Live Threads
`39c382c8-4585-817f-90e3-000cd221a0a0`, 💰 Price Discovery Study
`39c382c8-4585-812b-8a35-000cc323df37`.
**Never touch the old parenting DB** (`c6209e29-55ef-4781-b735-73b2a254e34f`) —
its live threads belong to `pipeline-tick`.

Full lifecycle, gates, and SQL: `docs/uae-track/01-crm-operating-spec.md`.
Email rules for everything drafted here: `haytham-email-draft` +
`references/uae-track.md`.

## 0 — Ceiling + today's send count, PER INBOX (compute first, everything else uses it)

Sends now leave from **two inboxes**, each its own domain with its own
reputation, its own ramp, and its own daily count. Everything in this
section is computed **once per inbox** and kept separate — never pooled.
The registry (`python main.py inbox list`, or `audit/inboxes.py`) maps the
logical labels to addresses and transports:

- **Inbox 1** = haytham@auto-mate.one — read/draft via the **Gmail MCP**
  tools (`search_threads`, `list_drafts`, `create_draft`). Primary; also
  carries the parenting track.
- **Inbox 2** = haytham@gethaytham.com — read/draft via the **direct API**:
  `python main.py gmail-gethaytham <search|drafts|draft>`. There is no
  Gmail MCP connector for this inbox.

**The ceiling:** run `python main.py send-cap status --all` and quote its
literal block (one ramp line per inbox + the additive total). Each inbox
ramps 20 → 25 → 30 and fails closed to 20 independently; when an inbox's
step has held 7 days it prints that inbox's RAMP REMINDER — surface it at
the top of the brief, naming the inbox. **Raising any cap is Haytham's
call, gated on THAT inbox's deliverability having actually held; this skill
NEVER runs `send-cap set`.**

**The day:** "today" is the **Dubai calendar day** (UTC+4, no DST) — the
same boundary `send_cap.py` uses. This tick fires at 02:53 UTC = 06:53
Dubai; compute the Dubai date string once and use it in every Gmail search
and SQL comparison below. Never mix server-local, UTC, and Gmail-account
days.

**The count — TOTAL sends leaving EACH inbox today** (warm replies,
parenting-track sends, and deliverability-test sends all count against
whichever inbox they left from). Start with `python main.py inbox counts`:
it counts the direct-API inboxes for you (Inbox 2 comes back as a real
number) and hands you the exact query for the Gmail MCP inboxes:

- **Inbox 2:** taken straight from `inbox counts` (`count` field).
- **Inbox 1:** run the `query` it prints (`in:sent after:<today>`) via the
  Gmail MCP and count the results, **plus** `in:scheduled` due today.
  **Scheduled sends sit in neither sent mail nor drafts until they depart;
  skipping this read overshoots the ceiling by exactly their count.**

Cross-check with the CRM, split by inbox (undercounts by design — one row
per lead, UAE only; Gmail wins on disagreement):

```sql
SELECT "Inbox" AS inbox, COUNT(*) AS sends
FROM "collection://5efbdd9b-1e19-468c-96db-f94a525846e0"
WHERE date("date:Last Contacted:start") = date('now', '+4 hours')
GROUP BY inbox
```

**The deliverability log:** skim `docs/deliverability-log.md` (bounces,
spam-folder hits, test scores). If a bounce or spam mention turns up below,
append it in the same run with `python main.py send-cap log --inbox
"<label>" --kind bounce|spam-flag|over-ceiling --detail "..."` — it writes
the one canonical, per-inbox line the ramp decision reads (don't hand-type
the line; the command enforces the shape and refuses a bad inbox/kind).
Commit and push the file change to uae-track if you make one.

**The budget — computed separately for each inbox, follow-ups first:** for
inbox X, count today's still-unsent follow-ups whose lead is assigned to X
(warm replies owed, discovery questions due, cold Touch 2/3 due) = F_X.
New-opener headroom on X = X's ceiling − X's sends so far − F_X. Openers
routed to X get what's LEFT on X — never what X's follow-ups need. Enforced
per lead by the gate invocations in steps 3 and 4, each passing
`--inbox "<the lead's Inbox>"` and that inbox's own `--sends-today`. Also
run the per-inbox 14-day history query from the operating spec and flag any
inbox over its own ceiling on any day as a deliverability risk.

## 0.5 — Gmail-state reconciliation (Scheduled / Draft Ready → reality)

The CRM's `Scheduled` and `Draft Ready` statuses mirror Gmail state, so
verify them against Gmail every morning. **Check each lead against the
inbox it's assigned to** (its `Inbox` property): Inbox 1 rows use the Gmail
MCP (`list_drafts`, `in:sent`); Inbox 2 rows use `python main.py
gmail-gethaytham drafts` and `... search "in:sent after:<today>"`. A draft
or sent message only "exists" for reconciliation if it's in the RIGHT
inbox — a Draft Ready Inbox 2 lead whose draft is in Inbox 1 is a
misrouted draft, not a confirmation. (Rows with a blank `Inbox` predate
routing — treat as Inbox 1, the historical inbox, and set the label.)

- **Scheduled rows:** if the message now appears in `in:sent`, flip the
  row to `Outreach Sent` with the REAL departure date as `Last Contacted`
  (+ `Touch #`, `Next Action` +3 days, Email Thread Log entry, **the
  Touch-1 `Findings Bank` flip `1. UNUSED` → `1. USED-T1` when the row has
  a bank, and clearing the pre-send `Notes` markers — `run
  haytham-hook-finder` / `then ask to draft` / `HELD ... log on send`** —
  i.e. the FULL confirmed-send checklist in `haytham-email-draft` SKILL.md,
  every field, not just the dates). If it's still in the scheduled queue,
  leave it. If it's in neither (he cancelled it), flip back to
  `Draft Ready` or `Audit Ready` per what Gmail shows and say so in the
  brief.
- **Draft Ready rows:** confirm an unsent draft to that address still
  exists (`list_drafts`). Draft gone + nothing in sent = he deleted it —
  flip back to `Audit Ready` and flag. Draft gone + message in sent =
  it departed; do the full send logging (same complete checklist: bank
  flip + Notes clear included, not just the dates).

These reconciliation flips record reality (like reply detection) and are
allowed without approval.

## 1 — Reply detection (Gmail → Notion)

**One sweep PER inbox, not one search per lead** (per-lead searches grow
linearly with threads out and were 16+ Gmail calls per tick by day two).
Replies land in whichever inbox sent the thread, so sweep both:

- **Inbox 1:** `in:inbox after:<last tick's Dubai date>` via the Gmail MCP.
- **Inbox 2:** `python main.py gmail-gethaytham search "in:inbox
  after:<last tick's Dubai date>"`.

Match sender addresses against the CRM's Email column (one SQL pull), and
only fetch the full thread for matches — from the inbox where the reply
landed. A matched lead's `Inbox` should equal the inbox that caught the
reply; if it doesn't, **reconcile it**: run `python main.py inbox reconcile
--current "<row Inbox>" --found-in "<inbox that caught it>"` and, on a `SET`
result, write that label to the row's `Inbox` (a thread can't move between
Gmail accounts, so the CRM label is the thing that's wrong — reality wins).
This is a reality-recording write, allowed like reply detection. A lead who
last replied before the sweep window is caught by the Last Contacted
cross-check below.

Query the CRM for rows with Touch # ≥ 1 and Status in
(Outreach Sent, Reply Received, Price Discovery Sent, Offer Sent,
Call Booked, Dormant) — this is both the match list for the sweep and
the stall check. For any matched row, fetch the Gmail thread and sync.

- New reply found and Notion doesn't reflect it → update: Status = Reply
  Received (or the later stage that actually applies), Sequence = Warm,
  and quote the reply verbatim in the brief. Append the reply verbatim to
  the lead page's Email Thread Log entry it answers (`Reply:` line).
- **A reply on a `Price Discovery Sent` lead IS the study data.** The
  moment it lands: log her answer VERBATIM into `Price Discovery Answer`
  (her exact words, her currency, her hedges — never summarized), set
  `Discovery Anchor` per the mapping in
  `haytham-email-draft/references/uae-track.md` (no number → `Refused to
  name`), and fill the page body's Price Discovery section. This is the
  one write that must never wait — an unlogged answer is the old
  pipeline's data hole all over again.
- A reply is the highest-priority item in the brief — warm threads are
  where the meetings come from.
- Also check for bounces (mailer-daemon in the thread): flag as bad
  address, set Notes first line, Status back to Qualifying.

Reply-detection updates (Status/Sequence on a real reply, verbatim reply
+ discovery-answer logging) are the ONLY Notion writes this skill makes
without approval — they record reality, they don't create outreach.

## 2 — The discovery ladder (this track's reason to exist)

Two queues, surfaced every tick:

**a) Due the discovery question** — Status = Reply Received, thread warm,
turn-two done or in motion. For each: draft the price discovery reply
(email type (e) in `haytham-email-draft`, canonical phrasings in
`references/uae-track.md` — one question, no price of ours, never after a
stall). Create the Gmail DRAFT as a reply in the existing thread, subject
unchanged, **in the lead's assigned inbox** (Inbox 1 → Gmail MCP
`create_draft` with `replyToMessageId`; Inbox 2 → `python main.py
gmail-gethaytham draft <to> <subject> <body> --thread-id <t>
--in-reply-to <msgid>`). A discovery reply is a send and counts against
that inbox's budget.

**b) Answer logged, offer unlocked** — Status = Price Discovery Sent with
`Price Discovery Answer` filled and `Discovery Anchor` set. For each:
dump the fresh row to JSON, run `python main.py crm-gate offer
<row.json>`, and surface the literal output line in the brief. PASS →
"ready for the money email — say the word." FAIL → what's missing. Do
not draft the money email unprompted — the offer is Haytham's trigger,
this tick just tees it up.

**Flag loudly:** any lead at `Offer Sent` whose `Price Discovery Answer`
is empty or whose anchor is `Not asked yet` — that state should be
impossible (the gate blocks it) and means a manual transition bypassed
the system. It goes at the top of hygiene.

## 3 — Due follow-ups

Query rows where Next Action ≤ today and Status not in (Won, Lost,
Disqualified).

For each due row, identify the touch type from Sequence + Touch # + Status
(cold Touch 2/3, warm bump, dormant back-from-the-dead, post-offer
silence handling) and draft it with the **haytham-email-draft** skill —
full loop, correct email type, mechanics cadence (cold: Touch 2 day 3,
Touch 3 day 9, then Dormant with a 2-3 week revival date, never Lost for
a cold no-reply, never a Touch 4; warm: every 2-3 days, up to 8-10
touches). Post-offer silence gets the disambiguating questions from
uae-track.md, never a re-send of the offer and never a weak closer.

**Cold Touch 2/3 must carry something new, and the gate checks it.**
Before drafting, pick the carrier honestly: `second-finding` only if the
row's `Findings Bank` has an UNUSED entry past #1 (the gate verifies);
otherwise `loom-offer` (natural Touch 2) or `disambiguating-question`
(natural Touch 3 closer). Dump the fresh row to JSON and run
`python main.py crm-gate send <row.json> --sends-today <THAT INBOX's total
incl. already-queued drafts> --touch 2|3 --carries <carrier> --inbox
"<the lead's Inbox>"` — the `--inbox` is the lead's assigned `Inbox` (a
follow-up is sticky; it goes out of the same inbox that opened the thread),
and `--sends-today` is that inbox's own count from step 0, not the pooled
total. Quote the literal gate line per queued follow-up, and make the draft
actually carry what was declared (gate.md checks). FAIL on the carrier
means the follow-up doesn't go out today as a bare bump; it gets a real
payload or it waits.

Then create the Gmail DRAFT automatically for the strongest variant, **in
the lead's assigned inbox** (Inbox 1 → Gmail MCP `create_draft`; Inbox 2 →
`python main.py gmail-gethaytham draft <to> <subject> <body>
[--thread-id ...] [--in-reply-to ...]`). One guard: check that inbox's
drafts first (Inbox 1 `list_drafts`; Inbox 2 `gmail-gethaytham drafts`),
and if an unsent draft to that address already exists there, do NOT stack a
second one; surface the old draft in the brief instead ("draft from <date>
still unsent — send, edit, or delete"). Warm replies are drafted as replies
in the existing thread (Inbox 1: `replyToMessageId`; Inbox 2:
`--thread-id` + `--in-reply-to`).

Cold follow-ups count against their own inbox's headroom — if one inbox's
due list exceeds that inbox's remaining headroom, prioritize warm threads
first, then cold touches by lead quality WITHIN that inbox, and say plainly
which cold touches rolled to tomorrow (and on which inbox). Headroom on one
inbox never covers overflow from the other.

Do NOT log or increment anything at draft time — a Gmail draft is not a
send. Only after Haytham confirms a send does the logging + property diff
happen (per the email-draft skill's rules).

## 4 — Send queue (Touch 1 openers)

Query Status in (Audit Ready, Draft Ready) with an Email set (the 📤
Send Queue view). For each candidate, in order:

1. `python main.py email-check <address> --name "<name>"` — quote the
   line. FAIL = the address is unusable (typo/dead domain/no-reply):
   flag "needs a real address" and skip the gate. This is a sanity
   re-check only: deliverability was already confirmed at the walk
   (`email-verify` → `Email Verified`), and the gate in step 2 enforces
   that flag. A row that reaches the queue with `Email Verified` unchecked
   is an edge case the gate will catch — hold it and flag "needs
   email-verify" rather than sending.
2. **Assign the inbox if the row's `Inbox` is blank.** Run `python main.py
   inbox route --current "<row's Inbox or empty>" --count "Inbox 1=<its
   count>" --count "Inbox 2=<its count>"` — it returns the same inbox for
   an already-assigned lead (sticky) or the emptiest inbox for a new one.
   Write the chosen label to the row's `Inbox` now (this is a routing
   write, allowed like reply-detection writes) so the assignment is durable
   and the draft lands in the right place. Increment that inbox's running
   count for the rest of this tick.
3. Dump the fresh row to JSON (with the assigned `Inbox`) and run
   `python main.py crm-gate send <row.json> --sends-today <the ASSIGNED
   inbox's total incl. today's already-queued drafts> --touch 1
   --followups-due <that inbox's F from step 0, minus its follow-ups
   already queued> --inbox "<assigned Inbox>"`. Only PASS rows enter
   today's queue — the gate holds openers behind that inbox's follow-ups,
   so a FAIL on headroom means the opener rolls to tomorrow (or, if the
   OTHER inbox has room and the lead is not yet sticky, re-routing it there
   is fine — re-run route excluding the full inbox). Quote one gate line
   per queued lead, showing its inbox.

Present as "ready to send today," grouped **by inbox**, then split by
status within each: `Draft Ready` (draft sitting in that inbox — send it)
vs `Audit Ready` (still needs haytham-hook-finder before a draft can
exist).

**Pacing:** hand each inbox's queue over in batches of **at most 10**,
spread across the day (e.g. morning / midday / late afternoon) — 20 sends
in a two-minute burst is a spam-filter signature even under the ceiling,
and this is per inbox. Scheduled sending (Inbox 1) is fine and counts via
step 0's scheduled read; the batch shape applies to it too.

If the send queue is empty or thin: say so, and point at the Walk Queue
count — the bottleneck is findings, not sends; the fix is walks
(batch-audit), not louder emails.

Flag any Audit Ready row with no Email as "needs address" with its Notes
line.

## 5 — Hygiene flags (report, don't auto-fix)

- `Offer Sent` with no verbatim answer/anchor (the impossible state — top
  of the list).
- Audit Ready without `Finding Verified` checked, without `Email Verified`
  checked, or `Finding Verified` checked on a Lane 2/3 row (all incoherent
  — Audit Ready now means both hard gates are set).
- Status Outreach Sent with Touch # = 0.
- **Outreach Sent with no matching message in Gmail's sent mail** — the
  status means the email actually left; no matching send = a logging
  error or a scheduled send logged as departed (should be `Scheduled`).
- **`Last Contacted` in the future** on any row not at `Scheduled` — a
  future date on a "sent" row is a logging error, full stop.
- Any Cold row with Touch # ≥ 4 — the cold sequence is three touches;
  a fourth means the cadence rules were bypassed.
- An Outreach Sent (or later) row that carries a `Findings Bank` whose
  spent entry still says `UNUSED` — Touch 1 spends #1, so ANY sent row with
  a bank whose `1.` reads `UNUSED` is a missed flip; a follow-up that
  carried a banked finding leaving its entry `UNUSED` is the same bug.
  (Confirmed-send logging missed the `USED-TN` flip — see
  `haytham-email-draft`. This is the highest-frequency drift; the bank flip
  on Touch 1 was historically skipped.)
- An Outreach Sent (or later) row whose `Notes` still carry a pre-send
  workflow marker — `run haytham-hook-finder`, `then ask to draft`, or
  `HELD ... log on send` — the send resolved it and confirmed-send logging
  should have cleared it.
- Stale warm threads: Sequence = Warm, no touch in > 4 days (the
  stalled-threads SQL in the operating spec).
- Qualifying rows older than a week with no walk in the page body.
- Any day in the last 14 over the send ceiling (Gmail count vs
  `send-cap status`).

## 6 — The scoreboard (weekly, two minutes, by LEAD never by message)

If 7+ days since the last scoreboard (check the HQ hub page or the last
brief): compute and append to the brief — unique leads cold-touched,
unique leads replied (reply rate by lead), discovery answers collected
(the study count), anchors above/at/below, offers out, closes. Rates by
lead, never by message-row — counting rows once inflated the old
pipeline's numbers and it mattered.

**Attribution splits (what the old track learned only after 125 leads):**
break replies out by `Finding Type`, `Source Channel`, and `Lane` — one
GROUP BY each over the replied rows vs sent rows. The old track's lesson
was that `Dead/stale element` carried most warm replies; this track
should confirm or kill that within 30 leads instead of 125, and the
channel split is what decides where top-up sourcing spends its fetches.

## The brief

One message, in this order: the per-inbox ceiling block
(`send-cap status --all`, with any ramp reminder), replies (verbatim, with
the suggested next move), discovery ladder (due the question / offer
unlocked), due follow-ups (with drafts, tagged by inbox), today's send
queue (grouped by inbox, with gate lines and each inbox's headroom math),
hygiene flags, scoreboard (weekly). If a section is empty, one line saying
so. If everything is empty: "Pipeline quiet —
nothing due today," and stop. Keep it scannable; he reads this before
coffee.

## Hard rules

- Drafts only. Never send. Never advance Touch #, Last Contacted, Next
  Action, or set Status = Outreach Sent for an email that hasn't actually
  departed — creating a Gmail draft is not a send. (Setting `Draft Ready`
  at draft time and the step 0.5 reconciliation flips are the sanctioned
  exceptions: they mirror Gmail reality, they don't claim a send.)
- Reply-detection, discovery-answer logging, the step 0.5 Gmail-state
  reconciliation, the step 4 `Inbox` assignment (routing a lead to a
  sending inbox), and the step 1 `Inbox` reconcile (correcting the label to
  where a thread physically lives) are the only unprompted Notion writes.
- `Price Discovery Answer` is verbatim or it is nothing. Never paraphrase,
  never tidy her grammar.
- Never draft a money email unprompted, and never while `crm-gate offer`
  says FAIL.
- Never queue past a **sending inbox's own** ceiling (`send-cap status
  --all`, fails closed to 20 per inbox), and always that inbox's follow-ups
  before its new openers. Ceilings are per inbox and additive, never
  pooled. The gate line — with `--inbox` — is the proof, quoted per lead.
- Never run `send-cap set`. Surface the per-inbox ramp reminder; raising
  any cap is Haytham's call, made by him, gated on THAT inbox's
  deliverability actually holding.
- Never queue a cold Touch 2/3 without a PASS on its `--carries` check,
  and never declare a carrier the draft doesn't actually contain.
- Never stack a second unsent draft to the same address in the same inbox.
- A lead's inbox is sticky: once `Inbox` is set, its whole thread (opener,
  follow-ups, warm replies, discovery, offer) stays on that inbox. Never
  move a live thread between inboxes.
- Never log in to or act as Haytham on any platform (Instagram included).
  Public read-only data is not the issue; acting as him is.
- Never touch the parenting DB — that's pipeline-tick's territory.
