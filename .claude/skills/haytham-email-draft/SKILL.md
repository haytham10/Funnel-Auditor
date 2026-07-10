---
name: haytham-email-draft
description: Draft cold outreach emails, follow-ups, warm replies, money emails (priced close offers), price/deposit-objection replies, trust-verification replies, and past-client reactivation emails in Haytham's voice and framework for parenting/faith-based coach leads. Use this skill WHENEVER drafting any outreach email, follow-up touch, turn-two reply, warm-thread message, priced close, objection reply, or re-engagement email to a coach lead or past client, even if the user just pastes a funnel finding and says "write the email" or "draft this one" without naming the framework. Also use when the user asks to fix, tighten, or rewrite an existing draft of one of these emails. This skill carries the full framework (Voice, Email OS, SMYKM, Drafting Doc, Grand Slam Offer v2) and real sent examples, so there is no need to fetch them from Notion.
---

# Haytham Email Draft

Draft outreach that reads like a real person who walked their funnel, admired the work, noticed a gap almost against his will, and cares enough to mention it. Not a freelancer running a play.

The whole problem this skill solves: the draft has to be right on the first try, without the user pushing. The way that happens is the draft passes a silent loop BEFORE the user ever sees it. The loop is: draft → burrito test → gate → identify specific failures → rewrite only the failing element → run gate again from the top → repeat until every check clears and the internal score is 10/10. Never show a draft that hasn't cleared the full loop. The user should never need to ask for a redo.

## The non-negotiable order of operations

Do these in sequence. Do not skip ahead to writing.

1. **Identify the email type first.** Before touching the input, name which of these this is: (a) cold Touch 1 opener, (b) cold follow-up (Touch 2-4), (c) warm bump/follow-up, (d) turn-two reply (they engaged, offering the Loom), (e) money email (a priced close), (f) objection reply (price, deposit, or trust/logistics question), or (g) past-client reactivation. This determines which sections of mechanics.md and gate.md apply. A money email and a cold opener are different products; don't draft one using the other's rules.

2. **Confirm you have the input.** You need: the lead's name, the niche, the verified finding (the leak or observation), and enough of the funnel walk to write a concrete line. If the user gave you a Notion lead page or pasted the walk, you have it. If the finding is vague ("they have a funnel problem"), ask for the specific thing on the specific page before writing. A bespoke email is impossible without a bespoke finding.

   **If the SMYKM hook cites specific IG post content** (a date, a quote, an
   engagement number, "her post about X") rather than something from her
   site copy: confirm the opener-finder's hand-off actually verified it —
   it should say the image was vision-pass-confirmed (`vision_manifest.json`
   shows `read: true`), not just "N screenshots read" as a round-number
   claim. If that confirmation isn't there, do not draft the hook as given.
   Either ask the opener-finder step to confirm the image first, fall back
   to a hook grounded in confirmed site copy, or ask Haytham directly to
   confirm the post's content before it goes anywhere near a Gmail draft.
   An email built on an unverified IG-post hook is exactly the failure this
   check exists to catch — a real draft once opened on a specific post's
   likes and comment-to-DM pricing that, per the session's own tool log,
   was never actually read.

3. **Read the reference files now, before drafting.** Read `references/voice.md`, `references/examples.md`, and `references/critical-failures.md` every time — the critical-failures file is mandatory corrections learned from repeated user corrections, not situational reading. Read `references/mechanics.md` if this is a follow-up, a turn-two reply, or a warm thread (the sequencing rules live there). Read `references/drafting-craft.md` if the finding is abstract and you need to make it concrete and falsifiable. These are short and they are what stop the draft from coming out generic.

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
  - First send on a lead: "Audit Ready" → "Outreach Sent".
  - Cold follow-up (Touch 2-4, still no reply): stays "Outreach Sent".
  - She replies for the first time: → "Reply Received" (this is also the Sequence flip point).
  - A Loom gets sent (turn-two default move): → "Loom Sent".
  - A call gets booked: → "Call Booked".
  - Cold sequence completes (Touch 4) with no reply: → "Dormant" (not "Lost"). Set Next Action to a "back from the dead" bump 2-3 weeks out. This is a cooldown-and-reopen lead, not a dead one — do not close the file on a thread that never got a first reply. (Corrected Jul 6, 2026 — the old "Touch 4 no reply → Lost" rule was the exact bug that buried ~22 real leads early; see The Bible Rule 8 scoping note. "Dormant" is a new pipeline status added specifically for this.)
  - She explicitly declines, or a warm thread (already replied at least once) goes cold through touch 8-10 with nothing further: → "Lost" (also set Lost Reason). "Lost" is reserved for an explicit no or a genuinely exhausted warm sequence — never for a cold thread that simply never got a first reply.
  - Payment confirmed / project starts: → "Won".
  If the send doesn't match any transition above (e.g. a warm bump that isn't a stage change), leave Status as-is, but still state that you checked it.
- **Last Contacted**: today, on every send.
- **Next Action**: the date depends on what was just sent, not just cold Touch 1 timing — check references/mechanics.md sequencing rules: cold Touch 1 → day 3-4, Touch 2 → day 6-7, Touch 3 → day 8-9, Touch 4 → no fifth cold touch, but set Next Action 2-3 weeks out for a back-from-the-dead bump rather than clearing it (see Status rule above). Warm thread (any touch after her first reply) → 2-3 days out, up to 8-10 touches. Turn-two, objection reply, or money email → set Next Action to whenever you'd expect to check back if she doesn't respond, using the warm cadence.

Before calling update_properties, state the full property diff (all five fields, old value → new value) so a missed field, or a Status that didn't actually change when it should have, is visible before the call, not after.

## What this skill does NOT do

It does not log to Notion before the user approves. Draft is not send. Do not make Notion tool calls during or after drafting unless the user explicitly says "log this" and pastes the final text.

It does not invent findings. If you do not have a verified, specific leak or observation, you stop and ask. A guessed finding produces a template email, and a template email is dead.

## Quick reference: the shape

- Subject: names the specific thing inside their world. Under 8 words, no end punctuation, sentence case (subject only, body uses proper capitalization). (Full subject rules in mechanics.md.)
- Line 1: the finding or the human hook, stated flat. No warm-up, no "I was browsing."
- The cost: what the gap is costing them, in something they can picture.
- The close: one real question they can answer in one line. An open door, not a bow.
- Sign off: none. Haytham has a signature configured in Gmail (name + Website link), so the draft body ends at the close, no name or sign-off needed.

The references hold the detail. Read them. The single most common failure is drafting from memory of these rules instead of reading them fresh, which is exactly how the generic version slips back in.
