# Critical failures — learned from repeated user corrections

These are the most common ways a draft that "passes" the gate on a shallow
read is still wrong. Each has been corrected before, sometimes more than
once. Internalize them before every draft — this is what `python main.py lint` cannot check for you: it catches an invented number or a lost claim, not a sentence that is technically legal and still reads like a machine.

## Three-beat parallel structures (banned)

The kill list bans "not just X, but Y, and Z." The rule extends to ANY
three-item parallel structure inside one sentence — three clauses, three
verbs, or three negatives in series, not just that exact phrasing.

**Violations (illustrative):**
- "The cohort is well built, the voice is consistent, and the niche has weight." — three clauses in one sentence.
- "11,500 people visit, leave, and never hear from you again." — three verbs in series.
- "They are not in your inbox, not on your list, and not reachable." — three parallel negatives.

**Fix:** break it into separate sentences. "The cohort is well built. The
voice is consistent. The niche has weight." Each period is a pause for the
reader. Multiple short sentences in a row is NOT a three-beat — a beat
requires parallel clauses stacked inside one sentence, not several short
sentences back to back.

## Formulaic transitions (banned)

These read as templates the moment a reader has seen a cold email before:

- "The thing that got me though" / "What I couldn't shake" / "The thing I noticed" — overused discovery frames.
- A templated pivot repeated across emails — a close is a real move once and a tell the second time it ships verbatim. The shape is fixed; the wording is not.
- "I noticed..." / "I wanted to reach out..." — already on the kill list, but watch for paraphrases that dodge the exact words while keeping the same discovery-frame shape.
- "Anyway, the reason I'm writing..." — a legitimate transition, but an option
  rather than a default. Don't reach for it on every draft.

**Fix:** say the thing flatly. No discovery frame, no "I went through your site
and found..." The fact, then what you took from it.

## Math breakdowns that read like a report

"8 meetings in 30 days, 3 of which signed, at an average of AED 12,000 each,
which works out to..." — this reads like a spreadsheet, not a person. It is an
operator-vocabulary violation in disguise even when no banned word appears,
because the *shape* of a breakdown is the giveaway.

**Fix:** one number is the backdrop, not the argument. "A health coach in Dubai
closed AED 78,000 from prospects I put in front of them." One number, one
outcome, done. Stacking three numbers in one sentence turns proof into a pitch
deck. The same instinct as drafting-craft's "small numbers, bigger timeframe",
applied to how many numbers land in one place rather than which ones.

## Subject-body disconnect

The subject has to be echoed in the first body sentence. If the subject is built
around a specific hook (a framework name, an episode title) and the first body
sentence goes somewhere else, the subject reads disconnected from the email
under it — she opened for one thing and landed on another.

**Fix:** the subject IS the hook compressed. Write the hook first, then cut it
down to under 8 words for the subject. Doing it the other way around is how
they drift apart.

## The email OS vs. voice tension, resolved for the hook

Mechanics says beat 1 is a specific, recent, cited fact. Voice says admire
first. Both are true, and here is how they resolve on an actual cold opener
rather than staying an abstract contradiction to re-derive every draft:

- The subject IS the hook, compressed.
- First body sentence: the cited fact. This is the admiration — attention paid
  is the admiration, not an adjective about it.
- Second clause, same paragraph: what you took from it. Without this the
  paragraph hands her back her own sentence and the next one has nowhere to
  start.

_(This section used to resolve the tension against a finding: sentence one
admires, sentence two states the leak flat. The finding is gone, and the
resolution is now internal to beat 1 — admiration and writer's clause in the
same breath.)_

## Motivation must feel real

Voice.md models stating the real motivation out loud: "I couldn't just sit
around and watch your work go underappreciated." Say why you're writing,
but keep it to one short line — the sentence right before it should have
already supplied the "it" the motivation line refers to, so it doesn't need
re-explaining. "I couldn't just watch it." is a complete, load-bearing
sentence when the prior sentence already put "people disappearing" in the
reader's head. Spelling out what "it" means again is padding — the burrito
test should catch that on its own, but it's a specific enough mistake to
name here.

## Warm replies are not this machine's job

The old repo carried a long section here on answering a warm reply without
reverting to opener craft — matching a five-word reply's length instead of
firing four paragraphs at it.

It is deliberately not carried over. This machine stops at an upload file, and
every reply lands in Smartlead where Haytham answers it by hand. If a reply
path is ever built back in, the rule to re-derive is the one that section
existed for: **match the reply's length and tone, answer the actual question,
make the next step one decision, then stop.**

## The close is an open door, not a bow

No "let me know." No "looking forward." No "if you're open to it." **And no
question about her business as the whole close.**

The close asks for fifteen minutes, carries a clock on the deliverable, and
names the one thing only a conversation can answer:

- Good: "15 minutes and they're yours the same day. I'll tell you why these 10
  and not the other 40."
- Good: "Give me 15 minutes this week and the 10 are in your inbox before the
  call ends."
- Bad: "Is that deliberate, or did it just never get built?" *(a question CTA
  selects for replies that are ANSWERS — a conversational dead end that looks
  like success and converts at zero. 4 of 4 openers closed this way; 0 calls.)*
- Bad: "Let me know if you'd like to chat about this."
- Bad: "15 minutes?" *(no clock, no reason. The ask survives and the thing that
  makes it worth accepting does not.)*

The deliverable does the work the two named times used to do: it turns a
request into an exchange. **Vary the phrasing per lead** — the shape is fixed,
the wording is not, and a close reused verbatim is a tell the second time it
ships.

_(Until 2026-07-31 this close named two specific times instead. That was right
for an offer that sold booked calls and wrong for one that hands over ten names:
a campaign cannot hardcode a weekday, since a Wednesday slot is wrong for
anything landing Thursday. If dated times come back, compute two per lead at
build time from the scheduled send date.)_
