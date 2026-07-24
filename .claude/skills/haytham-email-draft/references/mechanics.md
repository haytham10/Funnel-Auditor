# Mechanics — Email OS + SMYKM test layer

The channel rules and sequencing. Read this for any follow-up, turn-two reply, or warm thread.

## Confirmed principles (rules, not suggestions)

- **Outcome only, never features.** They don't care that you build Kajabi funnels. They care what they get. Lead with the result, not the credential.
- **Plain language, anyone should follow it.** No jargon, no insider terms, no industry shorthand. Write so a parent, a coach, or a stranger with zero context could read the email and immediately understand what's wrong and what they'd get. If a sentence needs specialized knowledge to land, simplify it. Result-driven over technical: say what it costs them or what they get, not how the mechanism works.
- **Keep the fix vague, name the finding specific.** The open loop pulls the reply. State what they get, leave the how as the question.
- **Short beats long** — as a default pressure. One finding, one cost, one question. (Voice overrides the cap when admiring properly needs the room.)
- **The finding is a trigger event.** A real leak is a reason to reach out now. You are not bothering people if you are relevant.
- **Plain text only.** No images, no HTML. No Loom link in email 1. No Calendly link in email 1. Every link signals a sales asset. Earn the reply first.
- **Never print a bare domain or email address in the body.** Gmail auto-links any bare `name.tld` or `a@b.com` into an ugly `https://www.google.com/url?q=...&source=gmail` tracking redirect, which reads as a spam signal in a personal email (it mangled a real Susan Koruthu draft, Jul 15 2026). Refer to a site by description instead ("your old site", "the FAQ page", "the new site") — the reader knows which of her pages you mean. Cold openers carry no links at all; if a link is genuinely intended (a money-email proof link), write it with an explicit `https://` scheme, never bare. This is code-enforced by a PreToolUse hook on `create_draft` (`.claude/hooks/gmail_draft_link_guard.py`) that blocks the draft if a bare domain/email is in the body — so a slip fails loudly instead of shipping.
- **One CTA only.** One question or one offer per email. Not a menu.
- **Exact numbers over ranges.** "$8,123 in one week" beats "multiple five figures."
- **Your opening email IS the lead magnet.** The finding you surface is real value given upfront. Don't withhold it for a call.
- **The reinforcement loop (COLD threads only).** On a thread that has never replied, each email rewards the last open. The finding in touch 1 is the reward that earns touch 2's open. Every COLD follow-up must deliver something new, even small. Dead-weight cold bumps ("just checking in") erode the loop. The value is the email; the ask rides on top. **This rule is scoped to cold.** Once a thread is warm (she replied), it flips: a warm reply answers what the person actually said and advances ONE step — it does NOT re-deliver the finding, the price, or the Loom. Re-stating what she already acknowledged reads as low-confidence and kills rapport (see the Warm replies section below). Do not let cold-follow-up logic bleed into warm threads.

## Subject line

Earns the open. Everything else is secondary.

**SMYKM rule (live test layer, running 90 days from Jun 24 2026):** the subject references something only this person would recognize — their own framework name, a phrase from their content, a specific episode title. It should make little sense to anyone else.

- Good: "the 2 choices framework", "your episode on eldest kids", "hello 35"
- Dead: "quick question", "I noticed something", "free audit for coaches"

Under 8 words. No end punctuation. No ALL CAPS. Sentence case. Human, not clever. Never change the subject line on a follow-up — same thread, same subject.

## Niche lingo swap (never use operator vocabulary)

- "clients" / "leads" -> whoever she actually serves, in her words (parenting track: parents, moms, families; UAE track: read her site and use HER noun for them — founders, professionals, women in leadership, whatever she calls them)
- "funnel" -> never say it; describe it in their terms
- "sequence" / "email sequence" -> never say it
- "email capture" / "opt-in" / "conversion" / "optimize" -> never say it
- "audit" -> "I went through your..."

Test: does it sound like a coach-adjacent human noticing something, or a consultant running a play?

## Body structure (the guide, not a script)

- Line 1: the finding or the SMYKM human hook, stated flat. No "I was browsing."
- The cost: what the gap costs them right now, in something they can picture.
- The close: one question or one concrete offer, never both.
- Sign off: "Haytham" on its own line. Required (Jul 14, 2026: the Gmail auto-signature was removed, so the body must carry the name itself). Every worked example in examples.md ends this way.

Two-line paragraphs. She is reading distracted on her phone. Build conflict in: what's there vs what's missing. The hidden "but" is the turn.

## SMYKM openings

- **A — elaborate the human hook**, then bridge to the finding. Needs a transition line: "anyway, the reason I'm writing..." or "what actually made me reach out though..." Only available when `haytham-hook-finder` has already written a real hook to the lead's Notion page (see SKILL.md step 2) — it's an upgrade, not something to construct from memory or a guess.
- **B — direct finding opener** (Lane 1, felt leak). No transition needed. Used once `haytham-hook-finder` has run and come up empty (`no hook found in IG evidence` on parenting-track rows, `no hook found in public evidence` on UAE rows) — a resolved state, not a shortcut. **Never draft in either opening while the Notion page's `SMYKM hook:` line still says "not run yet"** — that means the hook hasn't been looked for yet, not that one doesn't exist; see SKILL.md step 2 for the hard gate.

For Lane 2 (no felt leak), pre-handle the one objection in their head before they can say it. One sentence.

## Follow-up sequences

**Cold (never replied) — UAE track (the parenting track has no cold sequences left; its old 4-touch cadence is history):**
- Touch 1: opener, one finding — the #1 entry in the lead's Findings Bank.
- Touch 2: day 3, same subject/thread. Must carry something new (below).
- Touch 3: day 9, same subject/thread, final. Must carry something new; the disambiguating question is the natural closer here.
- After 3 with no reply: park (Status → "Dormant", not "Lost" — see SKILL.md). No fourth cold touch. Set a "back from the dead" bump 2-3 weeks out with a new angle, not another "just checking in." A dormant thread with a real Tier A/Lane 1 finding is an asset sitting in the pipeline, not a dead lead — reopening it costs nothing.

Do not stop at touch 1 — but a follow-up has to earn its place. Each cold send eats the day's inbox budget; a bare bump is a wasted send and a spam signal.

**What touches 2 and 3 must carry (enforced: `crm-gate send --touch N --carries …` blocks the queue slot without it).** Exactly one new thing per follow-up:
- **The next banked finding.** The walk banks every finding that survived both filters, ranked depth-first, in the row's `Findings Bank`; the gate checks an UNUSED entry past #1 actually exists (never invent one at draft time) and never draws the `RESERVED` deep finding — that one is held for the call, never a carrier. Name the second finding as a felt cost with its innocent explanation and KEEP THE FIX VAGUE — same rule as touch 1, and doubly so if it's a deep finding (name that it exists and costs her, never the mechanism or the fix). Naming a second cost is not the Adrienne mistake; teaching a second fix is (her thread died because touch 2 and 3 handed over three complete free diagnoses with nothing owed). The open loop is what pulls the reply.
- **The Loom offer.** One line, no price, no link on a cold thread: offer the walkthrough, don't attach it.
- **The disambiguating question.** Direct binary, no soft exit: "Should I stop following up, or is this still on your radar?"

The old "bump the same finding from a new angle" shape (the Heba thread) is retired as a follow-up on this track — time-passing framing is still good seasoning on top of a carrier, but it no longer qualifies as the payload. Anything beyond the banked findings still belongs in "The Next Three" bonus after a price is on the table, or in the Loom — a cold thread never gets taught fixes for free.

**Warm (replied once), when she goes quiet again:** follow up every 2-3 days, up to 8-10 touches. Short one-liners, pattern interrupts, a relevant result. Never repeat the same message. 80% of warm meetings come between follow-up 5-9. Follow-ups: under 7 words when possible. You are bumping, not re-pitching. This is the *quiet-again* cadence — for how to answer a reply the moment it lands, see the Warm replies section directly below.

## Warm replies (the turn-two craft)

The opener craft in this file is thick and the warm-reply craft used to be one line, so the model reverts to opener/pitch machinery the moment a reply lands: it re-lists the finding she already acknowledged, re-states price and guarantee, re-offers the Loom, and turns a five-word reply into a four-paragraph sequence. That is the single biggest warm-thread failure. This section is the antidote.

**The core rule: match the reply, answer it, advance one step, stop.**
- **Match length and tone.** A five-word reply gets a one-line answer. A blunt reply gets a blunt answer. A warm chatty reply can breathe a little. Mismatch reads as not-listening. (Research backs this hard: Lavender data — 150+ word emails are 42% less likely to get a reply than sub-50-word ones; Gong's 304k-email analysis — pitching after a reply cuts reply rates up to 57%.)
- **Once she's replied, the finding, the price, and the Loom have already done their job.** Re-stating them reads as low-confidence and kills rapport. Do not re-deliver what she already has. The reinforcement-loop rule (carry a new payload every touch) is COLD-only — it does not apply here.
- **Answer her actual question in one or two sentences, then stop.** No menu, no soft exit, no re-pitch. One concrete next step or one real answer.
- **The next step is ONE decision.** The default forward move is still the Loom offer, one line, no price, no options ("want me to record a quick 3-min walkthrough showing exactly what I'd fix? easier to show than explain") — but only when a next step is what the reply calls for. If she asked a question, the answer IS the move; don't bolt a Loom offer onto it.

The soft-exit reflex (trailing off with "no pressure, whenever") is one killer; the over-sell reflex (answering a short reply with a full pitch) is the other. Both lose the thread. Warm arcs that worked: Emily Ray (P3 — a small fix named in one line, the bigger finding held for the call), Donna (UAE 3 — the price-discovery reply), Helen (P2 — the priced close and the deposit flip). Read those in examples.md; don't duplicate their copy, match their restraint.

**Reply-type handling (good vs bad, all obeying every voice rule — no em-dashes, no kill-list phrases, proper capitalization):**

- **Blunt / testing** ("What do you want mate?"). Match the bluntness, drop the pitch, say the plain thing.
  - Good: "Fair. I spotted something on your booking page that's costing you sign-ups and I can show you the fix in a 3-min video. Worth a look?"
  - Bad: a four-paragraph reply that re-explains the finding, quotes the price and guarantee, and offers the Loom and a call. (This is the real failure that drew silence.)
- **Polite brush-off** ("thanks, we're all set" / "not right now"). Acknowledge, plant ONE doubt, leave the door open. Don't re-pitch.
  - Good: "Understood. The one thing I'd still glance at is whether that checkout works on mobile, most don't. If it's clean, ignore me."
  - Bad: "I understand, but let me explain everything my $200 package includes and why now is the right time..."
- **Price question** ("how much?"). Answer directly, do not dodge to a call. On this track the one price-discovery question comes first if it hasn't been asked (the flip: promise the number next message, then give it). Once discovery is done or not owed, name the flat track number. The "range" is the two tracks, not a haggle: Track A (735 AED) is the floor and happy price, Track B (2,575 AED) the ceiling; each is flat.
  - Good (discovery not yet asked): "I'll give you the exact number in my next message, promise. First, out of curiosity, what were you expecting it to cost?"
  - Good (discovery done): "735 AED flat, and if anything I touch isn't working when you check it, you pay nothing. Want me to start?"
  - Bad: "Depends on scope, let's hop on a call and I'll walk you through the packages." (Dodging a price question reads as hiding the price.)
- **Logistics / procurement question** ("what does it cover, where are you based, can I see proof?"). This is a buying signal, not a stall. Answer every question asked, in order, in one reply. Don't pad. Offer one or two real proof links, then offer to move to a faster channel, WhatsApp especially for UAE leads.
  - Good: "It covers the fixes plus a short recorded walkthrough. I'm based in Dubai. Proof: [one live client link with an explicit https://]. Easier on WhatsApp if you want, I'm on [number]."
  - Bad: a soft "great questions! happy to cover all that on a call" that answers none of them.
- **Five-scope-questions deflection** (a wall of questions used to stall). Don't answer all five in a wall of your own. Collapse to the one that actually decides it, answer that, and pull to a live channel.
  - Good: "The one that matters is timing: I can have it live and tested within 48 hours. The rest is easier to run through on a quick WhatsApp voice note than in email, want me to send one?"
  - Bad: a numbered list answering all five questions in six paragraphs (a wall answering a wall, nobody replies).

## Money emails (the priced close)

**UAE-track leads only: no money email exists until price discovery has run.** The discovery question goes out first (its own email type — see `references/uae-track.md`), the answer gets logged verbatim, and `python main.py crm-gate offer` must print PASS before a priced offer is drafted. This ordering is the entire point of the UAE track. Parenting-track warm threads are exempt (grandfathered mid-thread), but if a parenting thread is at the money moment and was never asked, asking first is still the better move.

This replaces the old "ask for a call, then negotiate" pattern entirely. Louise and Helen both stalled on vague scheduling asks with no price attached before either lead had a number to react to — do not repeat that shape. (Both threads later recovered once a flat price finally landed; see the Louise and Helen receipts in examples.md.) When it's time to close (after a Loom, or when a warm thread has earned it), the next email states a flat price and a payment path in the same message. No "do you have time" asks. No Calendly link as the close move.

**The offer (Grand Slam Offer v2, Jul 2 — read this before any money email):**

*Track A — The 48-Hour Rescue* (micro coaches, current pipeline, sub-10K audience, price-sensitive):
- One-liner: everything found gets fixed and live within 48 hours, she checks it herself, she only pays when it works.
- Price: $200 flat (or local equivalent — roughly £150; UAE leads always get 735 AED, never the dollar figure, never both currencies in one breath — see references/uae-track.md). The number never moves. (An earlier doc said 550 AED; that was a conversion error and would have been a silent 25% discount. 735 is the number.)
- Payment: default ask is half upfront to book the slot. If she hesitates on any upfront payment, fall back to full pay-after ("you check it, it works, then you pay") — this is a designed fallback, not the opener.
- Guarantee, stated boldly and unprompted: if anything touched isn't working when she checks it, she pays nothing and keeps every fix.
- Scarcity (true, because solo): one slot at a time.
- Bonuses available if she stalls (never lower the price instead): "The Next Three" — a short walkthrough of three more opportunities beyond the fixes ($150 value, free with the project); a one-page plain-language note of what changed and why.

*Track B — Launch-Ready, upgraded* (roster operators who already sell, real launch/sales numbers):
- Price: $700. Hold it.
- Headline guarantee: the order bump installed pays for the whole project within 30 days of her next launch, or the difference gets refunded. Receipt behind it: one bump did $522 on a single launch, 1 in 2 buyers took it.
- Delivery guarantee stacked under it: every fix live and tested before doors open, or she pays nothing and keeps the work.
- Bonuses matched to specific objections, never a discount: Launch-Week Hotline ($300 value, kills "what if something breaks"), Next Launch Playbook ($150 value, kills "then I depend on you forever"), Checkout Second Look 30 days post-launch ($200 value, kills "what if it doesn't work the first time").
- Closer of last resort (use only on a hard stall from a genuinely good fit, never lead with it): install the order bump for free, get paid only from what it makes.

**Field rules for every money email:**
1. The price never drops. Bonuses answer stalls. Term restructures answer term objections (see deposit/payment objections below). The unbundle answers scope objections. Three different moves, none of them a discount.
2. State the guarantee up front, boldly, before she can object. Naming the worst case unprompted is the strongest line available. Real receipt, current Track A price, Lisa Smith's Touch 3: "$200 flat covers the fix plus a short recorded walkthrough of those two along with what I'd do about them. If anything I touch isn't working when you check it, you pay nothing and keep everything anyway."
3. Proof rides with the offer: the PWH page links plus haytham-sys.netlify.app, so she can verify in 30 seconds this is real.
4. One CTA: the price and a single next step (a payment link, or "want me to start today"), not a menu.
5. Numbers stay locked to their real source: $8,123 and 93% are Birds & Bees only. $522 and the 50% take rate are Screen Smart order bumps only. 6.6% is the Hijab Workbook only. Never blur these across case studies.

## Small-deal closing (sub-$1k, Track A)

Track A is a small one-off deal ($200 / 735 AED). Small deals close differently from big ones: the buyer wants a fast, direct answer and a single low-risk decision, not a consultative dance. On a warm thread at the money moment:

- **Answer the price question directly.** For a sub-$1k deal, dodging "how much?" to a call reads as hiding the number and stalls the close. Give the flat figure. (The one exception is the price-discovery step, which asks what she'd pay BEFORE quoting — but that runs once, early, via the flip shape, and then you name the number in the very next message. Discovery is not a dodge; a call is.)
- **The "range" is the two tracks, never a within-track haggle.** If a range is useful framing, it's Track A (735 AED) as the floor and happy price, Track B (2,575 AED) as the ceiling, each flat. The number inside a track never moves (hard rule). A low anchor from her is market data, not permission to discount; answer objections with bonuses or a term restructure (GSO v2), never a lower number.
- **Attach the standing risk-reversal to every quote.** The guarantee rides with the price in the same breath, unprompted: "735 AED flat, and if anything I touch isn't working when you check it, you pay nothing." On a small deal the risk-reversal does more work than any feature list.
- **Offer a channel switch on a buying signal, WhatsApp especially for UAE.** A logistics or procurement question is a buying signal; after answering it, offer to move to WhatsApp or a quick voice note. UAE buyers close over WhatsApp far more readily than over email (Natavia receipt, trust-verification section).
- **After the ask, stop.** One decision on the table, then silence. Continuing to talk (adding a second reassurance, re-opening a doubt she didn't raise, stacking another bonus unprompted) reads as nerves and un-sells the close. Make the ask ONE decision and let it sit.

## The free-value cap (the gratitude trap)

Pam, Louise, and Helen all fixed the flagged issue themselves the same day and closed the loop with a thank-you instead of payment. That happens when too much gets diagnosed for free before any price is on the table. Cap free value at exactly: one opener finding, plus at most one Loom. Do not send a second or third finding into a thread that hasn't been priced yet — that's the specific mistake that lost Pam. If there's more to say, that's what "The Next Three" bonus is for, and it only gets shown after a price is already on the table, not before.

**The cap is on DEPTH too, not just count.** Findings come in two depths (see `haytham-opener-finder/references/walk.md`): shallow/self-fixable (a dead link, a test SKU, a form that should be a scheduler — she can fix it in minutes) and deep/un-self-fixable (pricing architecture, no owned audience, a whole program readable free — the reason to pay). The gratitude trap is worst when what's given free is *shallow*: she reads it, fixes it herself, thanks you, and is gone (Rita fixed her booking redirect, Avneet fixed her test-SKU checkout and logo). So:

- **Shallow findings can be named freely.** They earn the reply and cost nothing to give — that's their whole job as bait.
- **A deep finding's fix and full diagnosis are call-only.** In email you may NAME that a deeper issue exists and that it's costing her ("while I was in there I also found something bigger, on the pricing side"), but the how stays offline. Never hand over the mechanism or the fix of a deep finding in an email — that is the deep version of the gratitude trap, and it's worse, because a deep finding is the thing she'd actually pay to solve.
- **The `RESERVED` deep finding is held entirely.** The walk marks one deep finding RESERVED in the Findings Bank as the call bait; it is never emailed at all — not as an opener, not as a second-finding, not as a teaser fix. Naming that "something bigger" exists is the teaser (Emily Ray, P3 in examples.md); the finding itself and its fix are the reason for the call.

**Hard rule:** never hand over the fix or the full diagnosis of a deep finding in email. Name that it exists and that it's costing her, keep the how offline.

## Deposit / payment objections (warm, post-proposal)

When a warm lead objects to a deposit structure ("I wouldn't pay anyone in advance," "do job view pay"), this is a term objection, not a rejection of the project. Don't argue for the deposit or explain why it protects you. Accept the term and move the protection from money-first to speed-first instead: keep the scope exactly the same size, but reframe payment to land after delivery and verification ("you check it, it works, you pay"). The goal is closing the deal on her terms while keeping the work small enough that fast, unpaid delivery is low-risk for you.

Real receipt, current price: Helen's Touch 5, sent unprompted before any objection even arrived — "If half upfront is what's holding this up, happy to flip it. I get it all live first, you check it works, then you pay. Want me to start on that basis?" Louise's Touch 7 used the identical move. Neither has a confirmed reply yet, but this is the current shape and current price (£150 / 735 AED, both Track A) to draft from, not the older $400 version. The one confirmed acceptance on record is older ("No worries, that works fine... you check it, it works, and you pay the $400. Want me to start today?" — accepted and moved forward at the pre-GSO v2 price): the substance of the move (accept the term, keep scope the same, flip payment to land after delivery) is timeless even though that specific number is out of date.

## Trust-verification questions (warm, mid-negotiation)

When a warm lead asks logistics questions mid-negotiation, what exactly does the price cover, where are you based, can I see proof of your work, that's a buying signal, not a stall. Answer all questions asked, in the order asked, in one reply. Don't pad or soften. Offer one or two real proof links (your own site, a live client site). Then pivot the channel to something faster than email (WhatsApp, a call) rather than continuing to negotiate over more email turns.

Real receipt: Natavia asked what $400 covers, where Haytham is based, and for his website, in one message. The reply answered all three directly, gave two links, then offered to move to WhatsApp. She gave her number from her own site footer, no need to ask for it directly if it's already public. This is still the only confirmed trust-verification exchange on record, so it's the reference for now — note the $400 figure predates Grand Slam Offer v2 and would read as $200 (Track A) or $700 (Track B) today, but the mechanic (answer in order, offer proof, pivot the channel) hasn't changed.

## A numeric-contrast warning

If a SMYKM hook or opener involves two metrics the lead owns (e.g. a large podcast audience vs a small Instagram following), never put both numbers in the same sentence, even when the intent is to make the bigger number look good by comparison. The lead reads the smaller number as being pointed at, not the bigger one being praised. Lead with the strength alone. If the gap itself is part of the finding, find a way to name the cost it creates without restating both numbers side by side.

Real failure: a subject line built around "26k vs 1700" (podcast listeners vs IG followers) drew a one-word reply: "Rude." The underlying point (the podcast proves more trust than the smaller platform) was true and could have read as a compliment, but stating both numbers together read as a dig at the smaller one. No reply was sent back; once a lead reads an email as rude, there is no repair email that doesn't either over-apologize or escalate. Silence was correct.
