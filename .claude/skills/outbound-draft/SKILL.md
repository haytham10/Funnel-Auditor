---
name: outbound-draft
description: Write or fix a single cold email in Haytham's voice — the five beats, anchored on the hand-written lines, linted before it counts as done. Use WHENEVER Haytham asks to draft one email, rewrite a draft, fix a beat, tighten a line, or says "write this one", "how does this read", or pastes a draft and asks what is wrong with it. For a whole list use outbound-batch instead; this is the single-lead and the repair path.
---

# One email

Five beats, 67 to 95 words, and it has to read as though one person wrote it in
one sitting.

```
Hey {first name},

{hook}

{identity}

{offer}

{close}

Haytham

{ps}
```

Plain text. No links, no images, no price, no attachment.

## Read these first

They are the spec, not background:

- `references/voice.md` — the register, the kill list, what Haytham never says.
- `references/mechanics.md` — the email OS and the beat structure.
- `references/drafting-craft.md` — visualise, falsify, make it bespoke.
- `references/critical-failures.md` — AI tells that have shipped before.

**There is no examples file, deliberately.** No email in this shape has been
sent yet, so any worked example here would be a model's guess presented as an
exemplar — and since the whole design has you aligning to Haytham's hand-written
lines, a fabricated example would quietly become the thing you align to instead.
`copy/*.csv` is the real voice sample. When real emails have gone out and pulled
replies, the good ones become this file.

## The beats, ordered by the reader's objection

Each beat answers the objection raised at that exact moment. That ordering is
why the sequence is fixed.

**1 · Hook** — *"is this a spammer?"* One or two sentences about something
specific and recent she did, from real cited evidence. Rules in
`docs/hook-rules.md`. Never fabricated, and never her site's marketing copy.

**2 · Identity** — *"who is this and why should I care?"* Proof-based, never
title-based: a matched reference group, a real number, a timeframe. This beat
exists because two leads once replied trying to sell *to* Haytham — a warm,
specific email with no proof in it reads as someone looking for work.

**3 · Offer** — *"what can you do for me?"* Ten names, already pulled, for
people who fit her buyer profile. Fixed across the campaign.

**4 · Close** — *"what happens next?"* Fifteen minutes, a clock on the
deliverable, and why these ten and not the other forty. **That second half is
load-bearing.** Reply to call went 0 for 9 when the call held nothing that could
not have been typed in an email.

**5 · ps** — a costless no.

## The bridge

Between beat 1 and beat 2 the reader asks something the four-step frame does not
name: **"why are you telling me this?"** The hook just created context, so
jumping to a credential skips the question the hook itself raised.

**The identity line must turn to the reader before its first digit.** A
second-person clause ahead of the first number makes the proof hers instead of a
résumé line. This is a hard requirement, not a ratio — there is no lead for whom
a bare stat is the right second paragraph, and the linter fails a batch that
tries.

Do not collapse into one stock bridge either. "My job is finding your next
client." already opens 5 of 9 bridging lines; at volume that lands in one inbox
in six.

## The anchor

```
python main.py anchors <email> --coach-type <T> --sells-to <S>
```

Four hand-written lines, drawn deterministically for this lead. They are the
register and the claim set. You may re-voice one so it connects; you may not
change what it claims.

| Beat | Freedom | Must survive |
|---|---|---|
| Hook | yours to write | the cited fact |
| Identity | re-shape for the bridge | every digit, the segment, the timeframe |
| Offer | light re-voicing | ten names, already pulled, not a scraped list |
| Close | light re-voicing | 15 minutes, the clock, why these ten |
| ps | verbatim or near | the costless no |

Watch for re-voicing an anchor into blandness. "I pulled 10 names for you before
writing this" has a person in it; "I have identified ten prospects matching your
profile" has the same claim and no writer.

## Numbers

Every number must be true of a real client result, and the eight results live in
`copy/results.csv`. Never compute, round, combine or extrapolate. AED 78,000 does
not become "nearly 80k".

**Never relabel.** A segment's numbers may attach to that segment, or be widened
to "coaches here" with no segment named. A Business result described as a health
coach's is the tell that the whole email is fabricated, hook included — and
these coaches compare emails, so it surfaces.

Three honest ways to vary instead: **reframe** (same facts, different emphasis —
corporate readers get "somebody who could sign off the spend", individual
readers get the volume), **widen** (drop the segment, keep "coaches here"), and
**research proof** ("about a hundred coach sites, six published a price" — ours,
checkable, needs no client match at all).

## Before it counts as done

```
python main.py lint <draft.json>
```

Fix what it flags and run it again. Quote its PASS line rather than describing
it. A draft you have not linted is not a draft.

## Copy rules

No em-dashes, ever. No operator jargon — funnel, conversion, audit, sequence.
No weak closers: "no pressure", "no rush", "whenever timing's right". Proper
capitalisation. Sign off "Haytham" on its own line. Numbers with separators —
AED 36,000, never AED 36000, which reads as a merge field. Never a gendered
pronoun in an identity line; it fires across a whole segment and "her" is wrong
about half the time.

## What this skill will not do

Send anything. Invent a hook or a number. Quote a price — the money
conversation happens on the call, not in the inbox.
