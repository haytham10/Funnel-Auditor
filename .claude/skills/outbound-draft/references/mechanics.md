# Mechanics — the email OS

The channel rules. `voice.md` outranks this file when they collide.

_Rewritten 2026-07-31. The previous version was the funnel-audit OS: five beats
built around a finding and a cold read, plus sections on money emails, price
objections, deposits and warm-thread craft. All of that went with the offer.
What is left is the part that was never about the finding._

## Confirmed principles

- **Outcome only, never features.** She does not care how you find people. She
  cares that ten of them are already pulled.
- **Plain language.** A stranger with zero context should follow every sentence.
  If a line needs specialised knowledge to land, simplify it.
- **Arrive with something, don't reach for something.** The email's second job,
  after not reading as spam, is to make clear that work has already been done
  and is sitting there. That is what buys the fifteen minutes.
- **Keep the *how* vague, the *what* exact.** She gets ten names and why those
  ten. How they were found is the call.
- **Short beats long.** 67 to 95 words, mean around 80. Voice overrides the cap
  when admiring properly needs the room, but it rarely does.
- **Plain text only.** No images, no HTML, no attachment. No links at all in a
  cold opener — every link signals a sales asset. Earn the reply first.
- **Never print a bare domain or address in the body.** Mail clients auto-link
  any bare `name.tld` into a tracking redirect, which reads as a spam signal in
  a personal email. Refer to a page by description instead: "your about page",
  "the new site". `python main.py lint` blocks a draft that carries one.
- **One CTA only.** Fifteen minutes. A question about her business is legal only
  riding on the ask, never instead of it.
- **Exact numbers over ranges.** "AED 78,000" beats "high five figures". Every
  number must trace to `copy/results.csv`; see the fact table rule below.

## Subject line

Earns the open. Everything else is secondary.

The subject references something only this person would recognise — her own
framework name, a phrase from her content, a specific episode. It should make
little sense to anyone else.

- Good: "the 2 choices framework", "your episode on eldest kids", "hello 35"
- Dead: "quick question", "I noticed something", "free audit for coaches"

8 words or fewer. No end punctuation, no ALL CAPS, sentence case. Human, not
clever. Never a bare question — a question subject invites an answer, and an
answer is a dead end that looks like success.

## Niche lingo swap (never use operator vocabulary)

- "leads" / "prospects" → whoever she actually serves, in **her** noun. Read
  her site: founders, professionals, women in leadership, whatever she calls
  them.
- "funnel" → never say it.
- "sequence" / "campaign" / "outreach" → never say it.
- "conversion" / "optimise" / "pipeline" → never say it.
- "audit" → "I went through your..."

Test: does it sound like a coach-adjacent human who did some homework, or a
consultant running a play?

## Body structure

**Five beats, in this order, and the order is the order her objections arrive
in.**

```
BEAT 1  HOOK      something specific and recent she did, cited, plus what you
                  took from it. This is the admiration.       is this a spammer?
BEAT 2  IDENTITY  one sentence: who is writing and why he'd
                  know. Proof, never a title.                 why should I care?
BEAT 3  OFFER     ten names, already pulled.                  what can you do for me?
BEAT 4  CLOSE     fifteen minutes, a clock, and why these
                  ten and not the other forty.                what happens next?
Haytham
BEAT 5  ps        a costless no.
```

**Beat 2 exists because of two specific failures.** Lucia and Lee both replied
trying to sell *to* Haytham. A warm, specific, admiring email that asks about
someone's business with no statement of who is writing has one obvious reading:
this person wants to buy from me. Proof-based, never title-based.

**The bridge into beat 2 is the hardest thing in the email.** Between the hook
and the identity beat she asks something the four-step frame does not name:
*why are you telling me this?* The hook just created context, so jumping to a
credential skips the question the hook raised. **A second-person clause must
land before the first digit.** Not a ratio — there is no lead for whom a bare
stat is the right second paragraph, and the linter enforces it.

Do not collapse into one stock bridge. "My job is finding your next client."
already opens 5 of 9 bridging lines; at volume that lands in one inbox in six.

**Beat 4's second half is load-bearing.** "Why these ten and not the other
forty" is a question only a conversation can answer. Reply-to-call went 0 for 9
when the call held nothing that could not have been typed into an email. The
clock ("the same day", "before the call ends") is the `Y` in *X in Y time*, and
it is a real promise: the ten must exist and be handed over within a day, or
the first thing she can check is the first thing you broke.

Two-line paragraphs. She is reading distracted, on her phone.

Sign off "Haytham" on its own line. There is no auto-signature; the body carries
the name.

## The fact table

Every number in every email must be true of a real client result in
`copy/results.csv`. Eight segments, one result each.

**Never compute, round, combine or extrapolate.** AED 78,000 does not become
"nearly 80k". If a number would make the sentence better and is not in the
table, the sentence is wrong, not the table.

**Never relabel.** A segment's numbers attach to that segment, or are widened
with no segment named. "A health coach in Dubai closed AED 120,000" is a
Business result wearing a Health label. These coaches compare emails — 7 of 50
survivors on the last list were the same people arriving from two directories —
so it surfaces, and when it does the whole email reads as fabricated, hook
included.

**Three honest ways to vary instead:**

- **Reframe** — same facts, different emphasis. A corporate-facing reader gets
  "every one with somebody who could sign off the spend"; an individual-facing
  reader gets the volume.
- **Widen** — drop the segment, keep "coaches here". True of every lead. Weaker
  than an exact match, far stronger than a wrong one.
- **Research proof** — "about a hundred coach sites, six published a price."
  Ours, checkable, and needs no client match at all.

**No gendered pronouns in an identity line.** It fires across a whole segment
and "her" is wrong about half the time. Use "them".

**Format numbers with separators.** `AED 36,000`, never `AED 36000`, which
reads as an unfilled merge field.

## What is not here any more

Follow-up sequences, warm replies, money emails, price objections, deposit
objections and the credibility list all left with the funnel-audit offer.

Follow-ups are Smartlead sequence steps and are not built yet. Warm replies are
Haytham's, by hand, in Smartlead. No email this machine writes quotes a price.
