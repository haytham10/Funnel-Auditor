# The Gate — run silently before the user sees anything

This is the difference between "rules in a doc" and a draft that lands first try. Run every check. If any fails, rewrite and run again. Do not narrate this. Do not show a draft that hasn't cleared it.

## Voice core (outranks everything)

- [ ] Does it admire before it diagnoses?
- [ ] Does it help before it sells (earns belief, doesn't push a call)?
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
- [ ] One CTA only — one question or one offer, never both.
- [ ] Niche lingo: no operator vocabulary (funnel, sequence, opt-in, conversion, leads, optimize, audit).
- [ ] Conflict present: what's there vs what's missing.
- [ ] A real fact with a number where possible, not word-shaped air.
- [ ] Proper capitalization throughout, every sentence starts capitalized, "I" capitalized, normal grammar. Two-line paragraphs.
- [ ] Close is an open door, a real one-line-answerable question, not a neat bow.

## Cold follow-up specific (Touch 2 or 3 on a never-replied thread — there is no touch 4)

- [ ] Does the draft carry exactly ONE new thing: the next UNUSED entry from the row's `Findings Bank`, the leak-fix offer, or the disambiguating question? A draft that only bumps (time passing, "still there?", a re-ask) fails — a bare bump is a wasted send and a spam signal.
- [ ] Does what the draft carries MATCH what `crm-gate send --touch N --carries …` was told (and did it print PASS on a fresh row dump)? Declaring leak-fix-offer and drafting a bare bump is lying to the gate.
- [ ] If it carries a second finding: is it from the bank (never invented at draft time, never the RESERVED deep finding), named as a felt cost with its innocent explanation, fix left vague? Naming a second cost is fine; teaching a second fix is the Adrienne mistake (three complete free diagnoses, zero replies). If it's a deep finding, name that it exists and costs her, never the fix. Full fixes stay inside the paid Leak Fix or the Sprint bonus stack, after a price is on the table.
- [ ] If it carries the leak-fix offer: one line, the 500 AED paid-after fix, an offer not a link on a cold thread. Never the retired free Loom.
- [ ] If it carries the disambiguating question: direct binary, no soft exit ("Should I stop following up, or is this still on your radar?").
- [ ] Same subject, same thread as touch 1.

## Warm thread / turn-two specific (skip this section on a cold Touch 1)

- [ ] Does this draft actually move the deal forward, not just sound good? A warm thread where the lead has replied or shown buying signal needs a draft that advances toward a close (an offer, a concrete next step, an answer to a real question), not just a friendly reply that sounds finished but doesn't progress anything.
- [ ] If she objected to a term (price, deposit, timing), does the draft accept the term and adjust the structure around it, rather than arguing to keep the original term?
- [ ] If she asked logistics or trust questions, does the draft answer all of them directly before anything else?

## Turn-two specific (UAE track — the paid Leak Fix; see references/uae-track.md)

- [ ] Does the draft end in a single-tap next step or a paid tiny yes? Those are the ONLY two legal endings for a turn-two. Never a discovery question, never a menu, never a soft exit.
- [ ] If it offers the Leak Fix: 500 AED, access on their side, live in 48 hours, they pay only once it's working — stated in one breath, with the risk reversal attached?
- [ ] Is there a calendar link as the alternative single tap, with an explicit `https://` scheme (never a bare domain)?
- [ ] Is it NOT a free Loom offer? The Loom turn-two is retired (offered three times on this track, taken zero times).
- [ ] Did you resist gating this behind `crm-gate offer`? The Leak Fix is exempt — it's the rung that earns the Sprint number, not a priced offer that needs one.

## Price discovery email — RETIRED, do not draft one

- [ ] Is this a price discovery email? If yes, **stop**. The question was falsified as an email step on 2026-07-24 (100 touched leads, asked 3 times, 3 × `Refused to name`, 0 numbers). It no longer goes out over email.
- [ ] If they asked "how much?", does the draft answer with the number rather than flipping the question back at them? The flip is what produced two of the three refusals. Check `Asked For Price` on the row and quote the flat figure.

## Money email specific (any priced close, Track A or Track B)

- [ ] UAE lead: did `python main.py crm-gate offer` print PASS on a fresh row dump? No PASS, no money email — the lead must have EARNED a number, via an earned `Status` (`Call Booked`, `Leak Fix Sold`, `Leak Fix Delivered`, `Offer Sent`, `Won`) or the `Asked For Price` checkbox. (Parenting live threads are exempt. So is the 500 AED turn-two Leak Fix, which is not a money email for this purpose.)
- [ ] Does the draft state a flat price in the first close attempt — not a vague ask for time, not "do you have a minute to chat"?
- [ ] Is the price the correct track number ($200 / £150 for Track A, $700 for Track B; UAE leads get 735 AED / 2,575 AED, AED only, never both currencies) and not a number invented or negotiated down before she's even objected?
- [ ] UAE lead with a Below anchor OR a `Refused to name` anchor logged: does the draft lead even harder with the risk reversal (both say risk and trust are the objection, not the number), while the number stays exactly the track price?
- [ ] Are **BOTH named guarantees** stated boldly and unprompted, stacked, before any objection, not held back for if she pushes? The **Live-or-Free Guarantee** (live, tested from a clean device, taking bookings within 5 working days, or she doesn't pay and keeps the work) AND the **First Booking Guarantee** (no booking within 30 days of launch and the work continues free until there is one). "A guarantee" is not enough — name both.
- [ ] Does the First Booking Guarantee carry its condition ("you send traffic to it")? Dropping the condition to sound generous makes it unbounded and reads as desperate.
- [ ] Is the Sprint presented as the named stack ("The Booked-Out Funnel — 5-Day Sprint for UAE Coaches", 10,000 AED of components for 2,575 AED) rather than as "I'll fix your funnel for 2,575 AED"? The bare version is price-comparable to a Fiverr gig.
- [ ] Is the price 2,575 AED and not 3,600? The raise is gated on 2 closes and there are zero.
- [ ] Is there exactly one CTA — the price plus one concrete next step (payment link, "want me to start today")? Not a price plus a scheduling ask, that's two CTAs.
- [ ] Free-value cap (count): has this thread already had one opener finding plus at most one banked second finding? If a third piece of free diagnosis is about to be given before any price is on the table, stop — that is the gratitude-trap mistake, not a money email.
- [ ] Free-value cap (depth): does the draft hand over the fix or full diagnosis of a DEEP finding? It must not. Shallow findings may be named freely; a deep finding can only be NAMED as an existing cost, its fix kept offline. The `RESERVED` deep finding is never in an email at all. (See mechanics.md free-value cap.)
- [ ] If this is a bonus-stall response (she hesitated after a price was already given), does the draft add a named bonus or restructure a term, and leave the number itself untouched?
- [ ] Small-deal close (sub-$1k / Track A): if she asked "how much?", does the draft answer with the flat number directly rather than dodging to a call? (The one allowed detour is the single price-discovery question, which then names the number next message.)
- [ ] Does the standing risk-reversal ride with the quote in the same breath ("if it doesn't work, you pay nothing"), unprompted?
- [ ] On a logistics/procurement/trust question, does the draft offer a channel switch (WhatsApp, especially for a UAE lead) after answering?
- [ ] After the one ask, does the draft stop, no second reassurance, no re-opened doubt, no unprompted extra bonus?

## Length and imperfection

- [ ] Short by default. If it ran long, it ran long because the voice needed the room to admire properly, not because of padding. Cut anything that isn't doing work (the burrito test: pull a sentence out, does it still stand? then it shouldn't have been there).
- [ ] Not sanded to a robotic shine. A rough edge left in on purpose. Real, not performed.

Only after every box clears: deliver in the message composer.
