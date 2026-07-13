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

## 0 — Today's send count (compute first, everything else uses it)

```sql
SELECT COUNT(*) AS sends
FROM "collection://5efbdd9b-1e19-468c-96db-f94a525846e0"
WHERE date("date:Last Contacted:start") = date('now')
```

Remaining headroom today = **15 − sends** (the 12-15/day band is the
target, 15 is the hard ceiling — one inbox, one domain, no backup). Every
draft this tick queues for TODAY must fit inside that headroom, enforced
per lead by `python main.py crm-gate send <row.json> --sends-today N`.
Also run the 14-day history query from the operating spec and flag any
day over 15 as a deliverability risk.

## 1 — Reply detection (Gmail → Notion)

Query the CRM for rows with Touch # ≥ 1 and Status in
(Outreach Sent, Reply Received, Price Discovery Sent, Offer Sent,
Call Booked, Dormant). For each row with an Email, search Gmail for
threads with that address since Last Contacted.

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
stall). Create the Gmail DRAFT as a reply in the existing thread
(`replyToMessageId`), subject unchanged.

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
(cold Touch 2/3/4, warm bump, dormant back-from-the-dead, post-offer
silence handling) and draft it with the **haytham-email-draft** skill —
full loop, correct email type, mechanics cadence (cold: Touch 2 day 3-4,
Touch 3 day 6-7, Touch 4 day 8-9, then Dormant with a 2-3 week revival
date, never Lost for a cold no-reply; warm: every 2-3 days, up to 8-10
touches). Post-offer silence gets the disambiguating questions from
uae-track.md, never a re-send of the offer and never a weak closer.

Then create the Gmail DRAFT automatically for the strongest variant — with
one guard: check Gmail drafts first (`list_drafts`), and if an unsent
draft to that address already exists, do NOT stack a second one; surface
the old draft in the brief instead ("draft from <date> still unsent —
send, edit, or delete"). Warm replies are drafted as replies in the
existing thread (`replyToMessageId`).

Cold follow-ups count against today's headroom (they're cold sends) —
if the due list alone exceeds the remaining headroom, prioritize warm
threads first, then cold touches by lead quality, and say plainly which
cold touches rolled to tomorrow.

Do NOT log or increment anything at draft time — a Gmail draft is not a
send. Only after Haytham confirms a send does the logging + property diff
happen (per the email-draft skill's rules).

## 4 — Send queue (Touch 1 openers)

Query Status = Audit Ready with an Email set (the 📤 Send Queue view).
For each candidate, in order: dump the fresh row to JSON and run
`python main.py crm-gate send <row.json> --sends-today <count incl.
today's already-queued drafts>`. Only PASS rows enter today's queue, and
the queue stops at the headroom from step 0. Quote one gate line per
queued lead.

Present as "ready to send today." Remember these still need the hook
line resolved before a draft exists — split the queue into "draft
sitting in Gmail, ready to send" vs "needs haytham-hook-finder first."

If the send queue is empty or thin: say so, and point at the Walk Queue
count — the bottleneck is findings, not sends; the fix is walks
(batch-audit), not louder emails.

Flag any Audit Ready row with no Email as "needs address" with its Notes
line.

## 5 — Hygiene flags (report, don't auto-fix)

- `Offer Sent` with no verbatim answer/anchor (the impossible state — top
  of the list).
- Audit Ready without `Finding Verified` checked, or `Finding Verified`
  checked on a Lane 2/3 row (both incoherent).
- Status Outreach Sent with Touch # = 0.
- Stale warm threads: Sequence = Warm, no touch in > 4 days (the
  stalled-threads SQL in the operating spec).
- Qualifying rows older than a week with no walk in the page body.
- Any day in the last 14 with more than 15 sends.

## 6 — The scoreboard (weekly, two minutes, by LEAD never by message)

If 7+ days since the last scoreboard (check the HQ hub page or the last
brief): compute and append to the brief — unique leads cold-touched,
unique leads replied (reply rate by lead), discovery answers collected
(the study count), anchors above/at/below, offers out, closes. Rates by
lead, never by message-row — counting rows once inflated the old
pipeline's numbers and it mattered.

## The brief

One message, in this order: replies (verbatim, with the suggested next
move), discovery ladder (due the question / offer unlocked), due
follow-ups (with drafts), today's send queue (with gate lines and
headroom math), hygiene flags, scoreboard (weekly). If a section is
empty, one line saying so. If everything is empty: "Pipeline quiet —
nothing due today," and stop. Keep it scannable; he reads this before
coffee.

## Hard rules

- Drafts only. Never send. Never auto-advance Touch #, Status, Last
  Contacted, or Next Action for an unsent email — creating a Gmail draft
  is not a send.
- Reply-detection and discovery-answer logging are the only unprompted
  Notion writes.
- `Price Discovery Answer` is verbatim or it is nothing. Never paraphrase,
  never tidy her grammar.
- Never draft a money email unprompted, and never while `crm-gate offer`
  says FAIL.
- Never queue past 15 sends in a day. The gate line is the proof, quoted
  per lead.
- Never stack a second unsent draft to the same address.
- Never query or touch Instagram, and never act as Haytham on any
  platform.
- Never touch the parenting DB — that's pipeline-tick's territory.
