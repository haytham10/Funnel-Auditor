---
name: haytham-email-draft
description: Draft cold outreach emails, follow-ups, warm replies, price discovery replies (UAE track), money emails (priced close offers), price/deposit-objection replies, trust-verification replies, and past-client reactivation emails in Haytham's voice and framework, for both tracks — UAE coach leads (the active pipeline) and parenting/faith-based coach leads (live threads only). Use this skill WHENEVER drafting any outreach email, follow-up touch, turn-two reply, warm-thread message, price discovery question, priced close, objection reply, or re-engagement email to a coach lead or past client, even if the user just pastes a funnel finding and says "write the email" or "draft this one" without naming the framework. Also use when the user asks to fix, tighten, or rewrite an existing draft of one of these emails. This skill carries the full framework (Voice, Email OS, SMYKM, Drafting Doc, Grand Slam Offer v2, UAE pricing + price discovery) and real sent examples, so there is no need to fetch them from Notion.
---

# Haytham Email Draft

Draft outreach that reads like a real person who walked their funnel, admired the work, noticed a gap almost against his will, and cares enough to mention it. Not a freelancer running a play.

The whole problem this skill solves: the draft has to be right on the first try, without the user pushing. The way that happens is the draft passes a silent loop BEFORE the user ever sees it. The loop is: draft → burrito test → gate → identify specific failures → rewrite only the failing element → run gate again from the top → repeat until every check clears and the internal score is 10/10. Never show a draft that hasn't cleared the full loop. The user should never need to ask for a redo.

## The non-negotiable order of operations

Do these in sequence. Do not skip ahead to writing.

1. **Identify the track, then the email type.** Which CRM does this lead live in?
   - **UAE Lead CRM** (`collection://5efbdd9b-1e19-468c-96db-f94a525846e0`) — the active pipeline. Read `references/uae-track.md` before drafting anything for these leads: prices are quoted in AED (Track A 735, Track B 2,575, never a discount), the lifecycle differs, and one extra email type exists. The UAE worked examples at the top of `references/examples.md` are the anchor for these — pattern-match to them, not to the parenting examples below.
   - **Parenting Lead Pipeline** (`c6209e29-55ef-4781-b735-73b2a254e34f`) — live threads only, no new cold leads. Existing rules apply unchanged.
   Never log a lead into the other track's DB.

   Then name which of these the email is: (a) cold Touch 1 opener, (b) cold follow-up (Touch 2-3 on the UAE track, each carrying a declared payload — see references/uae-track.md; legacy parenting threads ran 2-4), (c) warm bump/follow-up, (d) turn-two reply (they engaged, offering the Loom), (e) **price discovery reply (UAE track only — the question that goes out BEFORE any priced offer, never after a stall; see references/uae-track.md)**, (f) money email (a priced close), (g) objection reply (price, deposit, or trust/logistics question), or (h) past-client reactivation. This determines which sections of mechanics.md, gate.md, and uae-track.md apply. A money email and a cold opener are different products; don't draft one using the other's rules.

   **UAE money-email hard gate:** for a UAE lead, a money email may not even be drafted until `python main.py crm-gate offer <row.json>` (row fetched fresh from Notion) prints PASS — verbatim discovery answer logged, anchor set. FAIL → stop, tell Haytham which piece is missing (usually: the discovery question hasn't gone out, or her answer was never logged). Quote the gate's literal output line either way.

2. **Confirm you have the input.** You need: the lead's name, the niche, the verified finding (the leak or observation), and enough of the funnel walk to write a concrete line. If the user gave you a Notion lead page or pasted the walk, you have it. If the finding is vague ("they have a funnel problem"), ask for the specific thing on the specific page before writing. A bespoke email is impossible without a bespoke finding.

   **Hard gate: do not draft until the hook has actually been looked for.**
   `haytham-opener-finder` only produces the lane, finding, and innocent
   explanation — it no longer finds a hook itself; that's
   `haytham-hook-finder`'s job. Check the Notion page's `SMYKM hook:` line
   before doing anything else:
   - `not run yet — see haytham-hook-finder` → **STOP. Do not draft.** Tell
     Haytham this lead needs `haytham-hook-finder` run first, and that you'll
     draft as soon as that line is resolved. This is a hard block, not a
     style note — do not proceed to Step 3 or write anything.
   - `no hook found in IG evidence — draft opens on the finding alone`
     (parenting rows) or `no hook found in public evidence — draft opens
     on the finding alone` (UAE rows) → `haytham-hook-finder` already ran
     and came up empty. This is a resolved state, not a missing input —
     proceed with **SMYKM opening B** (direct finding opener, no
     transition needed).
   - `<hook text> — WORK|LIFE|METRIC` → a real hook was found. Use
     **SMYKM opening A** (elaborate the hook, then bridge to the finding).

   If Haytham pastes a finding directly in chat with no Notion page behind
   it (no hook line to check at all), ask him whether a hook already exists
   for this lead before drafting — don't assume none does just because
   nothing was pasted.

   **If that hook line cites specific IG post content** (a date, a quote,
   an engagement number, "her post about X"): `haytham-hook-finder`
   already gates on `vision_manifest.json` showing that exact image
   `read: true` before writing it, so a hook present on the page has
   already cleared that check. If you have independent reason to doubt it
   (e.g. Haytham pasted a hook by hand in chat rather than through that
   skill), verify the same way before using it, or fall back to opening B.
   An email built on an unverified IG-post hook is exactly the failure
   this check exists to catch — a real draft once opened on a specific
   post's likes and comment-to-DM pricing that, per the session's own tool
   log, was never actually read.

3. **Read the reference files now, before drafting.** Read `references/voice.md`, `references/examples.md` (UAE examples first — that's the active track), and `references/critical-failures.md` every time — the critical-failures file is mandatory corrections learned from repeated user corrections, not situational reading. Read `references/mechanics.md` if this is a follow-up, a turn-two reply, or a warm thread (the sequencing rules live there). Read `references/drafting-craft.md` if the finding is abstract and you need to make it concrete and falsifiable. These are short and they are what stop the draft from coming out generic.

4. **See in the right order (this is the voice, not a style note).** Admire first: before the leak, see what they got right and feel it. Find the gap reluctantly: name it only because it genuinely helps. Help before sell: the email earns belief that you can help, it does not push a call. An email that diagnoses before it admires, or sells before it earns belief, is wrong no matter how clean the copy.

5. **Draft it.** One finding, one cost, one question or one offer. Plain text. No Loom or Calendly link in email 1. Proper capitalization throughout, every sentence capitalized, "I" capitalized, normal grammar. Default toward short, but length is a default pressure, not a hard cap: if the voice needs another two lines to admire properly before it diagnoses, take them. The voice wins over the word count when they conflict.

   Label this internally as Draft 1. Do not deliver it yet.

6. **Run the burrito test on every line.** Pull each sentence out. Ask: does the email still stand without it? If yes, the sentence is not earning its place. Cut it or rewrite it until it is. A sentence that exists only to connect two other sentences is padding. A sentence that exists because removing it collapses the email is load-bearing. Only load-bearing sentences stay.

   After the burrito test, fix everything that failed. This is now Draft 2 (or Draft 3, however many passes it takes). Do this silently.

7. **Run the full gate silently.** Check Draft 2+ against `references/gate.md` line by line. Do not skim. Every check must be ticked explicitly:
   - Voice core: admire before diagnose, help before sell, peer register, reads out loud like a real person
   - Kill list: zero violations, zero em-dashes, zero quoted-back words
   - Three drafting rules on every line: visualize, falsify, bespoke
   - Mechanics: subject SMYKM-grade, no operator vocab, one CTA, conflict present, sentence case
   - Critical failures per `references/critical-failures.md`: zero three-beat parallel structures (any three parallel clauses/verbs/negatives in one sentence, not just "not just X, but Y, and Z"), zero formulaic transitions, no math-breakdown-as-audit, subject echoed in the first body sentence, motivation stated without over-explaining, close is an open door not a bow

   If any check fails: identify the specific failure, rewrite only the failing element, run the full gate again from the top. Do not patch one line and assume the rest is fine. Keep iterating until every box clears.

   Before delivering, ask internally: is this a 10/10? A 9/10 is not good enough. The standard is: could this email only be sent to this specific person, and would a stranger who read it feel they were reading something real? If the answer to either is no, it is not done.

   Do all of this silently. Never show a failing draft. Never narrate the gate process to the user.

8. **Deliver in the message composer.** Use the message-composer tool with labeled variant tabs, not a plain text artifact. Subject line goes in the subject field. If you wrote more than one angle, each is its own labeled variant. Keep the labels goal-oriented (e.g. "Lane 1 direct", "SMYKM hook", "softer open").

9. **Wait for approval before logging anything.** Do not write to Notion after delivering the composer. The user picks a variant, tweaks if needed, then says "log" or "log this." If the user pastes edited final text, log that exact text. If the user says "log" without pasting anything, log the drafted variant as written (whichever variant they indicated), verbatim.

## Logging format (only after the user says "log this")

**Log to the lead's own CRM, never the other one.** UAE leads follow the
UAE lifecycle in `references/uae-track.md` (no "Loom Sent" status; the
artifact logs in the thread with an `Artifact:` line; Price Discovery
Sent and Offer Sent are their own statuses, and Offer Sent additionally
requires the `crm-gate offer` PASS). Parenting live threads follow the
status rules below unchanged. Touch #, Sequence, Last Contacted, and
Next Action mechanics are identical in both tracks. On a UAE cold Touch 1
log, also confirm the send passed `crm-gate send` with `--inbox "<the
lead's Inbox>"` (finding verified + follow-ups-first headroom under THAT
inbox's own ceiling + the touch 2/3 carrier check) — uae-tick normally ran
it at queue time; if this send bypassed the queue, run it now before
logging.

Before appending, fetch the lead's Notion page to confirm the current
literal body format — if you're appending via search-and-replace
(`update_content`), Notion's enhanced-markdown escaping (`\$`, auto-linked
domains) can break a naive match; escaped/non-plain formatting means use
`replace_content` (full body rewrite) instead. (Added Jul 10, 2026, after a
failed search-and-replace write forced a recovery fetch.)

Append to the lead's Notion page body under the Email Thread Log section in this exact format:

```
[Date] — Touch #N — Subject: "exact subject line" — Sent

[Verbatim email body]

Reply: No reply
Next: [specific next action + specific date]
```

At the same time, update ALL of these properties together in one call, not just Touch #:
- **Touch #**: increment by 1 from whatever it currently is, on every send — opener, follow-up, warm bump, turn-two reply, money email, objection reply, reactivation. Never leave it unchanged after a send.
- **Sequence**: "Cold" until she replies for the first time. The moment any reply lands, flip to "Warm" on that touch and it stays "Warm" from then on, even through objection replies or a money email later in the same thread.
- **Status**: reflects where the thread actually stands right now, updated on every send, not just the first:
  - First send on a lead: "Audit Ready" / "Draft Ready" / "Scheduled" → "Outreach Sent". (UAE track: "Draft Ready" = draft created in Gmail, set at draft time — the one status a draft is allowed to set; "Scheduled" = Haytham scheduled the send in Gmail. Both are pre-send states; "Outreach Sent" means the message actually departed, and Last Contacted is the real departure date, not the draft date.)
  - Cold follow-up (Touch 2-3 on the UAE track — there is no UAE Touch 4 — or a legacy parenting Touch 2-4, still no reply): stays "Outreach Sent".
  - She replies for the first time: → "Reply Received" (this is also the Sequence flip point).
  - A Loom gets sent (turn-two default move): → "Loom Sent".
  - A call gets booked: → "Call Booked".
  - Cold sequence completes (Touch 3 on the UAE track; Touch 4 on legacy parenting threads) with no reply: → "Dormant" (not "Lost"). Set Next Action to a "back from the dead" bump 2-3 weeks out. This is a cooldown-and-reopen lead, not a dead one — do not close the file on a thread that never got a first reply. (Corrected Jul 6, 2026 — the old "Touch 4 no reply → Lost" rule was the exact bug that buried ~22 real leads early; see The Bible Rule 8 scoping note. "Dormant" is a new pipeline status added specifically for this.)
  - She explicitly declines, or a warm thread (already replied at least once) goes cold through touch 8-10 with nothing further: → "Lost" (also set Lost Reason). "Lost" is reserved for an explicit no or a genuinely exhausted warm sequence — never for a cold thread that simply never got a first reply.
  - Payment confirmed / project starts: → "Won".
  If the send doesn't match any transition above (e.g. a warm bump that isn't a stage change), leave Status as-is, but still state that you checked it.
- **Last Contacted**: today, on every send.
- **Next Action**: the date depends on what was just sent, not just cold Touch 1 timing — check references/mechanics.md sequencing rules. UAE cold cadence: Touch 1 → +3 days (Touch 2 lands day 3), Touch 2 → +6 days (Touch 3 lands day 9), Touch 3 → no fourth cold touch, set Next Action 2-3 weeks out for the back-from-the-dead bump rather than clearing it (see Status rule above). Warm thread (any touch after her first reply) → 2-3 days out, up to 8-10 touches. Turn-two, objection reply, or money email → set Next Action to whenever you'd expect to check back if she doesn't respond, using the warm cadence.
- **Findings Bank** (UAE — any send that spent a banked finding, **Touch 1 included**): flip the entry the send carried from `UNUSED` to `USED-TN` in the `Findings Bank` property in the same update. **Touch 1 spends bank #1** — the opener always carries the strongest finding, so on a confirmed opener flip `1. UNUSED` → `1. USED-T1`; Touch 2/3 spend the entry declared to `crm-gate send --carries`. Draft time never touches the bank; confirmed-send logging is the only thing that spends an entry, and it runs on the opener too, not just follow-ups. Row with no `Findings Bank` (single-finding lead) → nothing to flip.
- **Notes** (UAE — clear the pre-send workflow markers this send just resolved): strip the operational to-dos left upstream by process-lead / opener-finder / the draft step — a `Hook not yet found — run haytham-hook-finder, then ask to draft` line, a `Ready for haytham-hook-finder` line, and the `Touch 1 ... HELD for manual send — log on send` held-draft marker — and replace the tail with `Sent Touch N <date>`. Keep the substantive walk/finding/email content; only the now-false pre-send instructions come out. A `run haytham-hook-finder` or `HELD ... log on send` line still sitting on an already-sent row is the exact hygiene drift this clears.

Before calling update_properties, state the full property diff (every field above — Touch #, Sequence, Status, Last Contacted, Next Action, and on the UAE track the `Findings Bank` entry spent and the `Notes` marker cleared — old value → new value) so a missed field, or a Status that didn't actually change when it should have, is visible before the call, not after. On a UAE send the bank flip and the Notes clear are part of this diff, not optional extras.

## What this skill does NOT do

It does not log to Notion before the user approves. Draft is not send. Do not make Notion tool calls during or after drafting unless the user explicitly says "log this" and pastes the final text. (One exception, UAE track: when a Gmail draft is actually created, setting Status = "Draft Ready" is allowed and expected — it mirrors Gmail state without claiming a send. Touch #, Last Contacted, Next Action, the Email Thread Log, and the Findings Bank still move only on a confirmed send.)

It does not invent findings. If you do not have a verified, specific leak or observation, you stop and ask. A guessed finding produces a template email, and a template email is dead.

It does not draft while the hook line still says "not run yet." Run `haytham-hook-finder` first (or confirm it already ran and came up empty) — see step 2 above.

## Quick reference: the shape

- Subject: names the specific thing inside their world. Under 8 words, no end punctuation, sentence case (subject only, body uses proper capitalization). (Full subject rules in mechanics.md.)
- Line 1: the finding or the human hook, stated flat. No warm-up, no "I was browsing."
- The cost: what the gap is costing them, in something they can picture.
- The close: one real question they can answer in one line. An open door, not a bow.
- Sign off: "Haytham" on its own line at the end. **Required** (changed Jul 14, 2026 — the Gmail auto-signature was taken down, so nothing supplies the name any more; an unsigned email now goes out genuinely unsigned). The rule was previously "no sign-off," which is why the worked examples in `references/examples.md` and this line disagreed for a while — the examples were right, the rule was stale.

The references hold the detail. Read them. The single most common failure is drafting from memory of these rules instead of reading them fresh, which is exactly how the generic version slips back in.
