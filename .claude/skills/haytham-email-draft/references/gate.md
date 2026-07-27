# The Gate — run silently before the user sees anything

This is the difference between "rules in a doc" and a draft that lands first try. Run every check. If any fails, rewrite and run again. Do not narrate this. Do not show a draft that hasn't cleared it.

## Voice core (outranks everything)

- [ ] Does it admire before it diagnoses?
- [ ] Does it help before it sells — is belief earned by everything above the close, so the call ask at the end is the payoff and not the pitch? (Reworded 2026-07-27: this used to read "doesn't push a call," which produced 9 replies and 0 calls. Asking is now correct; asking BEFORE earning is still wrong.)
- [ ] Peer register, never expert-above or pitch-below?
- [ ] Read out loud: sounds like Haytham talking to someone who trusts him, not written?

If any of these fail, the draft is wrong even if the copy is clean. Fix the seeing order first.

## Kill list scan

- [ ] None of: "stuck with me", "sitting/sat/stayed with me", "that's real", "love that/this/energy", "I noticed", "I wanted to reach out", "hope this finds you well", "no strings/worries/pressure", "just checking in", "quick question", "I came across your profile", "love what you're doing".
- [ ] No quoting her own words back to her.
- [ ] No em-dash anywhere. Not one.
- [ ] If two metrics she owns are being contrasted (a big number and a small one, both hers), the small one is never named alongside the big one, not in the body and not in the subject line. Lead with the strength only. (See the Darlynn example in examples.md for what this looks like when it goes wrong.)
- [ ] No three-beat parallel structure in any sentence ("not just X, but Y, and Z", or any three parallel clauses/verbs/negatives in one sentence — see references/critical-failures.md for examples of what this catches and doesn't).

## The three drafting rules (every line)

- [ ] Visualize: can she picture it? No abstract gap-talk.
- [ ] Falsify: is the finding checkable and specific? No adjectives for the leak.
- [ ] Bespoke: could a competitor sign this with the name swapped? If yes, rewrite.

## Mechanics

- [ ] Subject under 8 words, sentence case, no end punctuation, SMYKM-specific to this person.
- [ ] No Loom or Calendly link in email 1.
- [ ] No bare domain or email address in the body (Gmail auto-links it into a google.com/url redirect that reads as spam). Describe the site instead; intended proof links get an explicit https:// scheme. Enforced by the create_draft PreToolUse hook.
- [ ] One CTA only — and on a cold Touch 1 that CTA is a CALL ASK WITH TWO SPECIFIC TIMES. A question about her business is legal only as a second element riding on the call ask, never on its own.
- [ ] Niche lingo: no operator vocabulary (funnel, sequence, opt-in, conversion, leads, optimize, audit).
- [ ] Conflict present: what's there vs what's missing.
- [ ] A real fact with a number where possible, not word-shaped air.
- [ ] Proper capitalization throughout, every sentence starts capitalized, "I" capitalized, normal grammar. Two-line paragraphs.
- [ ] **Close is a next step with two named times, answerable in one word** — "I can call Tuesday around 4, or Wednesday morning, whichever is less annoying." An open door, not a neat bow, and not a question about her business. *(Changed 2026-07-27. All four UAE cold openers closed on a two-branch "is it X, or Y?" question and produced 0 calls between them: a question CTA selects for replies that are ANSWERS, and an answer is a conversational dead end that looks like success and converts at zero. Do not reword this back into a question.)*
- [ ] **Do the times vary from the last lead's?** The shape is fixed; the phrasing and the two times are not. A close reused verbatim is a tell the second time it ships — same rule as any other templated pivot line.
- [ ] **Beat 2 is a COLD READ from `references/cold-reads.md`, not a finding.** Is it phrased about the market ("most coaches here…") and not as an accusation about her ("you don't…")? The moment it names her as the one with the problem it is a finding again, with all the risk back.
- [ ] **Does the draft contain any number that is not on the credibility list or in the cold read's own stat?** If yes, cut it. Verified numbers only.
- [ ] **The identity beat: could this email be read as someone wanting to buy from her?** If yes, the beat is missing or too weak. (Lucia and Lee both replied with their own offer and pricing — they weren't confused about the finding, they were confused about who was writing. Two of nine failures caused by an absent sentence.)

## Cold follow-up specific (Touch 2 or 3 on a never-replied thread — there is no touch 4)

- [ ] Does the draft carry exactly ONE new thing: a SECOND cold read (a different pattern from the opener's), the call ask, or the disambiguating question? A draft that only bumps (time passing, "still there?", a re-ask) fails — a bare bump is a wasted send and a spam signal.
- [ ] Does what the draft carries MATCH what `crm-gate send --touch N --carries …` was told (and did it print PASS on a fresh row dump)? Declaring call-ask and drafting a bare bump is lying to the gate.
- [ ] If it carries a second cold read: is it from `references/cold-reads.md`, a DIFFERENT pattern from touch 1's, and phrased about the market rather than about her? **No finding, ever** — findings are RESERVED call bait and are never emailed at any touch, in any form, including as a teaser.
- [ ] If it carries the call ask: one line, two specific times, no link and no calendar URL on a cold thread. Never a fix offer, never a Loom (both retired 2026-07-27).
- [ ] If it carries the disambiguating question: direct binary, no soft exit ("Should I stop following up, or is this still on your radar?").
- [ ] Same subject, same thread as touch 1.

## Warm thread / turn-two specific (skip this section on a cold Touch 1)

- [ ] Does this draft actually move the deal forward, not just sound good? A warm thread where the lead has replied or shown buying signal needs a draft that advances toward a close (an offer, a concrete next step, an answer to a real question), not just a friendly reply that sounds finished but doesn't progress anything.
- [ ] If she objected to a term (price, deposit, timing), does the draft accept the term and adjust the structure around it, rather than arguing to keep the original term?
- [ ] If she asked logistics or trust questions, does the draft answer all of them directly before anything else?

## Turn-two specific (UAE track — the call ask; see references/uae-track.md)

- [ ] Does the draft end in a call ask with two named times? That is the ONLY legal ending for a turn-two. Never a discovery question, never a menu, never a soft exit.
- [ ] Does it name TWO specific times she can accept in one word ("Tuesday around 4, or Wednesday morning")? Not "do you have time this week" — an undated ask is the shape that stalled Louise and Helen.
- [ ] Is there NO calendar link sitting beside the times? Two named times plus "or here's my calendar" is a menu by this track's own definition, and the no-menu rule is written four times. Name the times, stop. (If a warm thread genuinely needs the link, it is `config.HAYTHAM_CALENDAR_URL`, always with an explicit `https://` scheme.)
- [ ] Is it NOT a fix offer and NOT a Loom? Both turn-two shapes are retired — the Loom was offered three times and taken zero, and the 500 AED Leak Fix went with the funnel-fix offer on 2026-07-27.
- [ ] Did you resist gating this behind `crm-gate offer`? The call ask is exempt — a booked call IS the rung that earns the number, so gating it would deadlock the motion it exists to start.

## Price discovery email — RETIRED, do not draft one

- [ ] Is this a price discovery email? If yes, **stop**. The question was falsified as an email step on 2026-07-24 (100 touched leads, asked 3 times, 3 × `Refused to name`, 0 numbers). It no longer goes out over email.
- [ ] If they asked "how much?", does the draft answer with the number rather than flipping the question back at them? The flip is what produced two of the three refusals. Check `Asked For Price` on the row and quote the flat figure.

## Money email specific (any priced close — The First Five)

- [ ] UAE lead: did `python main.py crm-gate offer` print PASS on a fresh row dump? No PASS, no money email — the lead must have EARNED a number, via an earned `Status` (`Call Booked`, `Offer Sent`, `Won`, or the legacy `Leak Fix Sold` / `Leak Fix Delivered`) or the `Asked For Price` checkbox. (Parenting live threads are exempt. So is the turn-two call ask, which is not a money email for this purpose.)
- [ ] Does the draft state a flat price in the first close attempt — not a vague ask for time, not "do you have a minute to chat"?
- [ ] Is the price 1,500 AED setup (credited against the first three calls) plus 600 AED per call that actually happens — AED only, never both currencies — and not a number invented or negotiated down before she's even objected?
- [ ] UAE lead with a Below anchor OR a `Refused to name` anchor logged: does the draft lead even harder with the risk reversal (both say risk and trust are the objection, not the number), while the number stays exactly the track price?
- [ ] Are **BOTH named guarantees** stated boldly and unprompted, stacked, before any objection, not held back for if she pushes? The **Live-or-Free Guarantee** (live, tested from a clean device, taking bookings within 5 working days, or she doesn't pay and keeps the work) AND the **First Booking Guarantee** (no booking within 30 days of launch and the work continues free until there is one). "A guarantee" is not enough — name both.
- [ ] Does the First Booking Guarantee carry its condition ("you send traffic to it")? Dropping the condition to sound generous makes it unbounded and reads as desperate.
- [ ] Is it presented as the named stack ("The First Five — 30 Days to a Booked Calendar", 14,100 AED of components) rather than as a flat fee for a service? The bare version is price-comparable to an agency retainer.
- [ ] Are BOTH guarantees named — the No-Show No-Charge Guarantee and Five or Free, with its 30-day condition intact? And exactly one true scarcity line ("I run four of these at a time")?
- [ ] Is there exactly one CTA — the price plus one concrete next step (payment link, "want me to start today")? Not a price plus a scheduling ask, that's two CTAs.
- [ ] Free-value cap (count): has this thread already had one opener finding plus at most one banked second finding? If a third piece of free diagnosis is about to be given before any price is on the table, stop — that is the gratitude-trap mistake, not a money email.
- [ ] Free-value cap (depth): does the draft hand over the fix or full diagnosis of a DEEP finding? It must not. Shallow findings may be named freely; a deep finding can only be NAMED as an existing cost, its fix kept offline. The `RESERVED` deep finding is never in an email at all. (See mechanics.md free-value cap.)
- [ ] If this is a bonus-stall response (she hesitated after a price was already given), does the draft add a named bonus or restructure a term, and leave the number itself untouched?
- [ ] If she asked "how much?", does the draft answer with the number directly rather than dodging to a call? Flipping the question back is what produced two of the three `Refused to name` answers.
- [ ] Does the standing risk-reversal ride with the quote in the same breath ("if it doesn't work, you pay nothing"), unprompted?
- [ ] On a logistics/procurement/trust question, does the draft offer a channel switch (WhatsApp, especially for a UAE lead) after answering?
- [ ] After the one ask, does the draft stop, no second reassurance, no re-opened doubt, no unprompted extra bonus?

## Length and imperfection

- [ ] Short by default. If it ran long, it ran long because the voice needed the room to admire properly, not because of padding. Cut anything that isn't doing work (the burrito test: pull a sentence out, does it still stand? then it shouldn't have been there).
- [ ] Not sanded to a robotic shine. A rough edge left in on purpose. Real, not performed.

Only after every box clears: deliver in the message composer.
